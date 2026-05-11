from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.governance.service import GovernanceService
from app.core.logging import get_logger
from app.llm.base import BaseLLMProvider
from app.memory.service import MemoryService
from app.models.api import ChatRequest, ChatResponse
from app.observability.tracing.models import SpanKind
from app.observability.service import ObservabilityService
from app.orchestration.events import EventPublisher
from app.orchestration.pipeline import ExecutionPipeline, PipelineExecutionState
from app.orchestration.pipeline.handlers import (
    AgentSelectionHandler,
    AuditHandler,
    ContextInitializedHandler,
    GovernancePhaseHandler,
    LLMGenerationHandler,
    PromptAssemblyHandler,
    RequestReceivedHandler,
    ResponseCompletedHandler,
    ResponseSynthesisHandler,
    RetrievalPhaseHandler,
    ToolDecisionHandler,
    ToolExecutionHandler,
)
from app.orchestration.pipeline.lifecycle import PipelineLifecycleManager
from app.orchestration.lifecycle.service import OrchestrationLifecycleService
from app.orchestration.planners.service import PromptAssemblyService
from app.orchestration.routing.service import DeterministicRequestRouter
from app.rag.retriever import RetrieverService
from app.tools.service import ToolExecutionService


class TurnExecutionService:
    def __init__(
        self,
        settings: Settings,
        llm_provider: BaseLLMProvider,
        retriever_service: RetrieverService,
        memory_service: MemoryService,
        tool_execution_service: ToolExecutionService,
        governance_service: GovernanceService,
        observability_service: ObservabilityService,
        event_publisher: EventPublisher,
        request_router: DeterministicRequestRouter,
        prompt_assembly_service: PromptAssemblyService,
        lifecycle_service: OrchestrationLifecycleService,
    ) -> None:
        self._settings = settings
        self._llm_provider = llm_provider
        self._retriever_service = retriever_service
        self._memory_service = memory_service
        self._tool_execution_service = tool_execution_service
        self._governance_service = governance_service
        self._observability_service = observability_service
        self._event_publisher = event_publisher
        self._request_router = request_router
        self._prompt_assembly_service = prompt_assembly_service
        self._lifecycle_service = lifecycle_service
        self._pipeline = ExecutionPipeline(
            stages=[
                RequestReceivedHandler(settings=settings, observability_service=observability_service, event_publisher=event_publisher),
                ContextInitializedHandler(lifecycle_service, governance_service),
                RetrievalPhaseHandler(retriever_service, memory_service, governance_service, event_publisher=event_publisher),
                GovernancePhaseHandler(governance_service, event_publisher=event_publisher),
                AgentSelectionHandler(event_publisher=event_publisher),
                ToolDecisionHandler(request_router, event_publisher=event_publisher),
                ToolExecutionHandler(tool_execution_service, governance_service, event_publisher=event_publisher),
                PromptAssemblyHandler(prompt_assembly_service, governance_service, observability_service=observability_service, event_publisher=event_publisher),
                LLMGenerationHandler(llm_provider, observability_service=observability_service, event_publisher=event_publisher),
                ResponseSynthesisHandler(lifecycle_service, memory_service),
                AuditHandler(observability_service),
                ResponseCompletedHandler(lifecycle_service, governance_service, event_publisher=event_publisher),
            ],
            lifecycle_manager=PipelineLifecycleManager(observability_service=observability_service, event_publisher=event_publisher),
        )
        self._logger = get_logger(__name__)

    async def run(self, session: AsyncSession, request: ChatRequest) -> ChatResponse:
        state = PipelineExecutionState(session=session, request=request)
        async with self._observability_service.span(
            "orchestration.run",
            kind=SpanKind.INTERNAL,
            component="orchestration",
            agent_name=request.agent_name or "conversation",
        ):
            result = await self._pipeline.run(state)
        return result.to_chat_response()

    async def stream_run(self, session: AsyncSession, request: ChatRequest) -> AsyncIterator[str]:
        state = PipelineExecutionState(session=session, request=request)
        queue: asyncio.Queue[str] = asyncio.Queue()

        async def emit(token: str) -> None:
            await queue.put(self._lifecycle_service.format_sse({"type": "token", "delta": token}))

        async def run_pipeline():
            async with self._observability_service.span(
                "orchestration.stream_run",
                kind=SpanKind.INTERNAL,
                component="orchestration",
                agent_name=request.agent_name or "conversation",
            ):
                return await self._pipeline.run(state, stream_callback=emit)

        task = asyncio.create_task(run_pipeline())
        while True:
            if task.done() and queue.empty():
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.05)
            except TimeoutError:
                continue
            yield event

        result = await task
        yield self._lifecycle_service.format_sse(
            {
                "type": "done",
                "conversation_id": result.context.conversation_id,
                "citations": [citation.model_dump() for citation in result.context.citations],
                "provider": result.provider_name,
                "model": result.model_name,
                "orchestration": result.orchestration.model_dump(mode="json"),
            }
        )