from __future__ import annotations

import json
from collections.abc import AsyncIterator
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.governance.base import GovernanceContext
from app.governance.service import GovernanceService
from app.core.logging import get_logger
from app.llm.base import BaseLLMProvider
from app.memory.service import MemoryService
from app.models.api import ChatRequest, ChatResponse, GovernanceSummary, OrchestrationMetadata, ToolExecutionRequest, ToolInvocationSummary
from app.observability.service import ObservabilityService
from app.orchestration.lifecycle.service import OrchestrationLifecycleService
from app.orchestration.planners.service import PromptAssemblyService
from app.orchestration.routing.service import DeterministicRequestRouter
from app.orchestration.state.models import OrchestrationRuntimeState, TurnContext
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
        self._request_router = request_router
        self._prompt_assembly_service = prompt_assembly_service
        self._lifecycle_service = lifecycle_service
        self._logger = get_logger(__name__)

    async def run(self, session: AsyncSession, request: ChatRequest) -> ChatResponse:
        async with self._observability_service.span("orchestration.run", agent_name=request.agent_name or "conversation"):
            turn = await self.prepare_turn(session, request)
        user_message = await self._lifecycle_service.store_message(
            session,
            conversation_id=turn.conversation.id,
            role="user",
            content=request.message,
            citations=[],
            metadata_json={"orchestration_trace_id": turn.trace_id, "agent_name": request.agent_name},
        )
        await self._memory_service.remember_user_message(
            session,
            conversation_id=turn.conversation.id,
            message_index=user_message.message_index,
            content=request.message,
        )
        if turn.blocked_response_text is not None:
            response_text = turn.blocked_response_text
            provider_name = "governance"
            model_name = "policy-engine"
        else:
            async with self._observability_service.span("llm.generate", provider=self._llm_provider.provider_name):
                response_text = await self._llm_provider.generate(turn.messages)
            provider_name = self._llm_provider.provider_name
            model_name = self._llm_provider.chat_model
        await self._lifecycle_service.store_message(
            session,
            conversation_id=turn.conversation.id,
            role="assistant",
            content=response_text,
            citations=turn.citations,
            metadata_json={
                "orchestration_trace_id": turn.trace_id,
                "tool_used": turn.orchestration.tool_invocation.model_dump() if turn.orchestration.tool_invocation else None,
                "agent_name": request.agent_name,
            },
        )
        await self._lifecycle_service.commit_turn(session)
        return ChatResponse(
            conversation_id=turn.conversation.id,
            response=response_text,
            citations=turn.citations,
            provider=provider_name,
            model=model_name,
            orchestration=turn.orchestration,
        )

    async def stream_run(self, session: AsyncSession, request: ChatRequest) -> AsyncIterator[str]:
        async with self._observability_service.span("orchestration.stream_run", agent_name=request.agent_name or "conversation"):
            turn = await self.prepare_turn(session, request)
        user_message = await self._lifecycle_service.store_message(
            session,
            conversation_id=turn.conversation.id,
            role="user",
            content=request.message,
            citations=[],
            metadata_json={"orchestration_trace_id": turn.trace_id, "agent_name": request.agent_name},
        )
        await self._memory_service.remember_user_message(
            session,
            conversation_id=turn.conversation.id,
            message_index=user_message.message_index,
            content=request.message,
        )

        if turn.blocked_response_text is not None:
            response_text = turn.blocked_response_text
            yield self._lifecycle_service.format_sse({"type": "token", "delta": response_text})
            provider_name = "governance"
            model_name = "policy-engine"
        else:
            accumulated: list[str] = []
            async with self._observability_service.span("llm.generate_stream", provider=self._llm_provider.provider_name):
                async for token in self._llm_provider.generate_stream(turn.messages):
                    accumulated.append(token)
                    yield self._lifecycle_service.format_sse({"type": "token", "delta": token})
            response_text = "".join(accumulated)
            provider_name = self._llm_provider.provider_name
            model_name = self._llm_provider.chat_model
        await self._lifecycle_service.store_message(
            session,
            conversation_id=turn.conversation.id,
            role="assistant",
            content=response_text,
            citations=turn.citations,
            metadata_json={
                "orchestration_trace_id": turn.trace_id,
                "tool_used": turn.orchestration.tool_invocation.model_dump() if turn.orchestration.tool_invocation else None,
                "agent_name": request.agent_name,
            },
        )
        await self._lifecycle_service.commit_turn(session)
        yield self._lifecycle_service.format_sse(
            {
                "type": "done",
                "conversation_id": turn.conversation.id,
                "citations": [citation.model_dump() for citation in turn.citations],
                "provider": provider_name,
                "model": model_name,
                "orchestration": turn.orchestration.model_dump(mode="json"),
            }
        )

    async def prepare_turn(self, session: AsyncSession, request: ChatRequest) -> TurnContext:
        trace_id = self._observability_service.current_trace_id() or str(uuid4())
        runtime_state = OrchestrationRuntimeState(
            trace_id=trace_id,
            agent_name=request.agent_name or "conversation",
            conversation_id=request.conversation_id,
        )
        conversation = await self._lifecycle_service.get_or_create_conversation(session, request.conversation_id)
        runtime_state.conversation_id = conversation.id
        runtime_state.record("conversation_resolved", conversation_id=conversation.id)

        async with self._observability_service.span("retrieval.search", conversation_id=conversation.id):
            retrieval = await self._retriever_service.search(session, request.message)
        runtime_state.record("retrieval_completed", retrieval_count=len(retrieval.citations))

        async with self._observability_service.span("memory.build_context", conversation_id=conversation.id):
            memory = await self._memory_service.build_context(
                session,
                conversation_id=conversation.id,
                query=request.message,
            )
        runtime_state.record("memory_loaded", memory_count=len(memory.relevant_memories))

        tool_plan = self._request_router.route(request.message, retrieval)
        governance_context = GovernanceContext(
            trace_id=trace_id,
            agent_name=runtime_state.agent_name,
            conversation_id=conversation.id,
            message=request.message,
            requested_tool=tool_plan.name if tool_plan else None,
            tool_arguments=tool_plan.arguments if tool_plan else {},
            metadata={
                "retrieval_count": len(retrieval.citations),
                "memory_count": len(memory.relevant_memories),
                "stream": request.stream,
            },
        )
        async with self._observability_service.span("governance.evaluate", requested_tool=governance_context.requested_tool):
            governance_decision = await self._governance_service.evaluate(governance_context)
        runtime_state.record(
            "governance_evaluated",
            allowed=governance_decision.allowed,
            reason=governance_decision.reason,
            requires_approval=governance_decision.requires_approval,
        )

        tool_response_text = None
        tool_invocation = None
        blocked_response_text = None
        if not governance_decision.allowed:
            runtime_state.record("governance_blocked", violations=list(governance_decision.violations))
            blocked_response_text = self._blocked_response(governance_decision)
            tool_plan = None
        elif tool_plan is not None:
            runtime_state.selected_tool = tool_plan.name
            async with self._observability_service.span("tool.execute", tool_name=tool_plan.name):
                tool_response = await self._tool_execution_service.execute(
                    session,
                    ToolExecutionRequest(name=tool_plan.name, arguments=tool_plan.arguments),
                )
            tool_invocation = ToolInvocationSummary(
                name=tool_response.name,
                status=tool_response.status,
                trace_id=tool_response.trace.trace_id,
            )
            tool_response_text = json.dumps(tool_response.model_dump(mode="json"), ensure_ascii=True)
            runtime_state.record("tool_executed", tool_name=tool_plan.name, status=tool_response.status)
        else:
            runtime_state.record("tool_skipped")

        messages = []
        if blocked_response_text is None:
            async with self._observability_service.span("prompt.assemble", retrieval_count=len(retrieval.citations), memory_count=len(memory.relevant_memories)):
                messages = self._prompt_assembly_service.build_messages(request.message, retrieval, memory, tool_response_text)
            runtime_state.record("prompt_assembled", message_count=len(messages))
        else:
            runtime_state.record("prompt_skipped_due_to_governance")

        orchestration = OrchestrationMetadata(
            trace_id=trace_id,
            retrieval_count=len(retrieval.citations),
            memory_count=len(memory.relevant_memories),
            tool_invocation=tool_invocation,
            governance=GovernanceSummary(
                allowed=governance_decision.allowed,
                reason=governance_decision.reason,
                requires_approval=governance_decision.requires_approval,
                requested_tool=governance_context.requested_tool,
                approval_status=governance_decision.approval.status if governance_decision.approval else None,
                audit_record_id=governance_decision.audit_record.record_id if governance_decision.audit_record else None,
                violations=list(governance_decision.violations),
            ),
        )
        self._logger.info(
            "orchestration_prepared",
            extra={
                "trace_id": trace_id,
                "conversation_id": conversation.id,
                "retrieval_count": len(retrieval.citations),
                "memory_count": len(memory.relevant_memories),
                "tool_name": tool_plan.name if tool_plan else None,
                "agent_name": runtime_state.agent_name,
                "steps": [step.name for step in runtime_state.steps],
            },
        )

        return TurnContext(
            trace_id=trace_id,
            conversation=conversation,
            retrieval=retrieval,
            memory=memory,
            citations=retrieval.citations,
            messages=messages,
            orchestration=orchestration,
            tool_response_text=tool_response_text,
            blocked_response_text=blocked_response_text,
            runtime_state=runtime_state,
        )

    def _blocked_response(self, decision) -> str:
        if decision.requires_approval:
            return "This request requires approval before execution."
        return "This request was blocked by governance policy."