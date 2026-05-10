from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.governance.service import GovernanceService
from app.llm.base import BaseLLMProvider
from app.memory.service import MemoryService
from app.models.api import ChatRequest, ChatResponse
from app.observability.service import ObservabilityService
from app.orchestration.execution.service import TurnExecutionService
from app.orchestration.lifecycle.service import OrchestrationLifecycleService
from app.orchestration.planners.service import PromptAssemblyService
from app.orchestration.routing.service import DeterministicRequestRouter
from app.rag.retriever import RetrieverService
from app.tools.service import ToolExecutionService


class OrchestrationService:
    def __init__(
        self,
        settings: Settings,
        llm_provider: BaseLLMProvider,
        retriever_service: RetrieverService,
        memory_service: MemoryService,
        tool_execution_service: ToolExecutionService,
        governance_service: GovernanceService,
        observability_service: ObservabilityService,
    ) -> None:
        self._execution_service = TurnExecutionService(
            settings=settings,
            llm_provider=llm_provider,
            retriever_service=retriever_service,
            memory_service=memory_service,
            tool_execution_service=tool_execution_service,
            governance_service=governance_service,
            observability_service=observability_service,
            request_router=DeterministicRequestRouter(),
            prompt_assembly_service=PromptAssemblyService(),
            lifecycle_service=OrchestrationLifecycleService(),
        )

    async def run(self, session: AsyncSession, request: ChatRequest) -> ChatResponse:
        return await self._execution_service.run(session, request)

    async def stream_run(self, session: AsyncSession, request: ChatRequest) -> AsyncIterator[str]:
        async for event in self._execution_service.stream_run(session, request):
            yield event