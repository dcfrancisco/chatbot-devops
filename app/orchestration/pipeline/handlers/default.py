from __future__ import annotations

import json

from app.governance.base import GovernanceDecision
from app.governance.interceptors import GovernanceInterceptorContext, GovernanceTarget, InterceptionPhase
from app.governance.service import GovernanceService
from app.llm.base import BaseLLMProvider
from app.memory.service import MemoryService
from app.models.api import GovernanceSummary, OrchestrationMetadata, ToolExecutionRequest, ToolInvocationSummary
from app.observability.service import ObservabilityService
from app.observability.tracing.models import SpanKind
from app.orchestration.events import EventPublisher, RuntimeEventName
from app.orchestration.context import DefaultExecutionContextBuilder
from app.orchestration.lifecycle.service import OrchestrationLifecycleService
from app.orchestration.pipeline.execution import PipelineExecutionState, PipelineStage
from app.orchestration.pipeline.stages import BasePipelineStageHandler
from app.orchestration.planners.service import PromptAssemblyService
from app.orchestration.routing.interfaces import RequestRouter
from app.rag.retriever import RetrieverService
from app.tools.service import ToolExecutionService


class RequestReceivedHandler(BasePipelineStageHandler):
    stage = PipelineStage.REQUEST_RECEIVED

    def __init__(self, *, settings, observability_service: ObservabilityService, event_publisher: EventPublisher | None = None) -> None:
        self._settings = settings
        self._observability_service = observability_service
        self._event_publisher = event_publisher

    async def handle(self, state: PipelineExecutionState) -> None:
        context = DefaultExecutionContextBuilder(
            settings=self._settings,
            observability_service=self._observability_service,
            request_message=state.request.message,
            conversation_id=state.request.conversation_id,
            user_id=None,
            agent_name=state.request.agent_name,
        ).build()
        state.context = context.transition(
            stage=self._execution_stage(),
            step_name=self.stage.value,
            metadata={"stream": state.request.stream},
        )
        if self._event_publisher is not None:
            await self._event_publisher.publish_runtime(
                context=state.context,
                event_name=RuntimeEventName.REQUEST_STARTED,
                stage=self.stage.value,
                metadata={"stream": state.request.stream},
            )

    def _execution_stage(self):
        from app.orchestration.context import ExecutionStage

        return ExecutionStage.REQUEST_RECEIVED


class ContextInitializedHandler(BasePipelineStageHandler):
    stage = PipelineStage.CONTEXT_INITIALIZED

    def __init__(self, lifecycle_service: OrchestrationLifecycleService, governance_service: GovernanceService) -> None:
        self._lifecycle_service = lifecycle_service
        self._governance_service = governance_service

    async def handle(self, state: PipelineExecutionState) -> None:
        assert state.context is not None
        workflow_context = GovernanceInterceptorContext(
            trace_id=state.context.trace_id,
            agent_name=state.context.agent_name,
            conversation_id=state.context.conversation_id,
            user_id=state.context.user_id,
            message=state.request.message,
            target=GovernanceTarget.WORKFLOW_EXECUTION,
            phase=InterceptionPhase.PRE_EXECUTION,
            workflow_name="chat-turn",
            metadata={"pipeline_stage": self.stage.value},
        )
        workflow_decision = await self._governance_service.intercept_pre_execution(workflow_context)
        state.governance_decision = workflow_decision.governance_decision
        state.context = state.context.with_governance_decision(workflow_decision.governance_decision)
        if not workflow_decision.allowed:
            raise RuntimeError(workflow_decision.governance_decision.reason)
        conversation = await self._lifecycle_service.get_or_create_conversation(state.session, state.request.conversation_id)
        state.context = state.context.with_conversation(conversation).with_runtime_attributes({"conversation_id": conversation.id})


class RetrievalPhaseHandler(BasePipelineStageHandler):
    stage = PipelineStage.RETRIEVAL_PHASE

    def __init__(self, retriever_service: RetrieverService, memory_service: MemoryService, governance_service: GovernanceService, event_publisher: EventPublisher | None = None) -> None:
        self._retriever_service = retriever_service
        self._memory_service = memory_service
        self._governance_service = governance_service
        self._event_publisher = event_publisher

    async def handle(self, state: PipelineExecutionState) -> None:
        assert state.context is not None and state.context.conversation is not None
        retrieval_context = GovernanceInterceptorContext(
            trace_id=state.context.trace_id,
            agent_name=state.context.agent_name,
            conversation_id=state.context.conversation_id,
            user_id=state.context.user_id,
            message=state.request.message,
            target=GovernanceTarget.RETRIEVAL_ACCESS,
            phase=InterceptionPhase.PRE_EXECUTION,
            metadata={"pipeline_stage": self.stage.value, "query_length": len(state.request.message)},
        )
        retrieval_decision = await self._governance_service.intercept_pre_execution(retrieval_context)
        state.governance_decision = retrieval_decision.governance_decision
        state.context = state.context.with_governance_decision(retrieval_decision.governance_decision)
        if not retrieval_decision.allowed:
            state.response_text = self._blocked_response(retrieval_decision.governance_decision)
            state.provider_name = "governance"
            state.model_name = "policy-engine"
            state.context = state.context.with_blocked_response(state.response_text)
            return
        if self._event_publisher is not None:
            await self._event_publisher.publish_runtime(
                context=state.context,
                event_name=RuntimeEventName.RETRIEVAL_STARTED,
                stage=self.stage.value,
                metadata={"query_length": len(state.request.message)},
            )
        retrieval = await self._retriever_service.search(state.session, state.request.message)
        await self._governance_service.intercept_post_execution(
            retrieval_context.with_phase(
                InterceptionPhase.POST_EXECUTION,
                metadata={"retrieval_count": len(retrieval.citations)},
            )
        )
        memory_context = GovernanceInterceptorContext(
            trace_id=state.context.trace_id,
            agent_name=state.context.agent_name,
            conversation_id=state.context.conversation_id,
            user_id=state.context.user_id,
            message=state.request.message,
            target=GovernanceTarget.MEMORY_ACCESS,
            phase=InterceptionPhase.PRE_EXECUTION,
            metadata={"pipeline_stage": self.stage.value},
        )
        memory_decision = await self._governance_service.intercept_pre_execution(memory_context)
        state.governance_decision = memory_decision.governance_decision
        state.context = state.context.with_governance_decision(memory_decision.governance_decision)
        if not memory_decision.allowed:
            state.response_text = self._blocked_response(memory_decision.governance_decision)
            state.provider_name = "governance"
            state.model_name = "policy-engine"
            state.context = state.context.with_blocked_response(state.response_text)
            return
        memory = await self._memory_service.build_context(
            state.session,
            conversation_id=state.context.conversation.id,
            query=state.request.message,
        )
        await self._governance_service.intercept_post_execution(
            memory_context.with_phase(
                InterceptionPhase.POST_EXECUTION,
                metadata={"memory_count": len(memory.relevant_memories)},
            )
        )
        state.retrieval = retrieval
        state.memory = memory
        state.context = state.context.with_retrieval(retrieval).with_memory(memory).with_runtime_attributes(
            {
                "retrieval_count": len(retrieval.citations),
                "memory_count": len(memory.relevant_memories),
            }
        )
        if self._event_publisher is not None:
            await self._event_publisher.publish_runtime(
                context=state.context,
                event_name=RuntimeEventName.RETRIEVAL_COMPLETED,
                stage=self.stage.value,
                metadata={"retrieval_count": len(retrieval.citations), "memory_count": len(memory.relevant_memories)},
            )

    def _blocked_response(self, decision: GovernanceDecision) -> str:
        if decision.requires_approval:
            return "This request requires approval before execution."
        return "This request was blocked by governance policy."


class GovernancePhaseHandler(BasePipelineStageHandler):
    stage = PipelineStage.GOVERNANCE_PHASE

    def __init__(self, governance_service: GovernanceService, event_publisher: EventPublisher | None = None) -> None:
        self._governance_service = governance_service
        self._event_publisher = event_publisher

    async def handle(self, state: PipelineExecutionState) -> None:
        assert state.context is not None
        context = state.context.to_governance_context(
            requested_tool=None,
            tool_arguments={},
            metadata={
                "retrieval_count": len(state.context.retrieved_documents),
                "memory_count": len(state.context.memory_entries),
                "stream": state.request.stream,
            },
        )
        decision = await self._governance_service.evaluate(context)
        state.governance_decision = decision
        state.context = state.context.with_governance_decision(decision)
        if self._event_publisher is not None:
            await self._event_publisher.publish_runtime(
                context=state.context,
                event_name=RuntimeEventName.GOVERNANCE_CHECKED,
                stage=self.stage.value,
                metadata={"allowed": decision.allowed, "requires_approval": decision.requires_approval, "reason": decision.reason},
            )


class AgentSelectionHandler(BasePipelineStageHandler):
    stage = PipelineStage.AGENT_SELECTION_PHASE

    def __init__(self, event_publisher: EventPublisher | None = None) -> None:
        self._event_publisher = event_publisher

    async def handle(self, state: PipelineExecutionState) -> None:
        assert state.context is not None
        state.selected_agent = state.request.agent_name or state.context.agent_name
        state.context = state.context.with_runtime_attributes({"selected_agent": state.selected_agent})
        if self._event_publisher is not None:
            await self._event_publisher.publish_runtime(
                context=state.context,
                event_name=RuntimeEventName.AGENT_SELECTED,
                stage=self.stage.value,
                metadata={"agent_name": state.selected_agent},
            )


class ToolDecisionHandler(BasePipelineStageHandler):
    stage = PipelineStage.TOOL_DECISION_PHASE

    def __init__(self, request_router: RequestRouter, event_publisher: EventPublisher | None = None) -> None:
        self._request_router = request_router
        self._event_publisher = event_publisher

    async def handle(self, state: PipelineExecutionState) -> None:
        assert state.context is not None
        if state.governance_decision is not None and not state.governance_decision.allowed:
            state.tool_plan = None
            return
        if state.retrieval is None:
            state.tool_plan = None
            return
        state.tool_plan = self._request_router.route(state.request.message, state.retrieval)
        state.context = state.context.with_runtime_attributes(
            {"requested_tool": state.tool_plan.name if state.tool_plan else None}
        )
        if self._event_publisher is not None and state.tool_plan is not None:
            await self._event_publisher.publish_runtime(
                context=state.context,
                event_name=RuntimeEventName.TOOL_REQUESTED,
                stage=self.stage.value,
                metadata={"tool_name": state.tool_plan.name, "arguments": state.tool_plan.arguments},
            )


class ToolExecutionHandler(BasePipelineStageHandler):
    stage = PipelineStage.TOOL_EXECUTION_PHASE

    def __init__(self, tool_execution_service: ToolExecutionService, governance_service: GovernanceService, event_publisher: EventPublisher | None = None) -> None:
        self._tool_execution_service = tool_execution_service
        self._governance_service = governance_service
        self._event_publisher = event_publisher

    async def handle(self, state: PipelineExecutionState) -> None:
        assert state.context is not None
        decision = state.governance_decision
        if decision is not None and not decision.allowed:
            state.response_text = self._blocked_response(decision)
            state.provider_name = "governance"
            state.model_name = "policy-engine"
            state.context = state.context.with_blocked_response(state.response_text)
            return

        if state.tool_plan is None:
            return

        tool_governance_context = state.context.to_governance_context(
            requested_tool=state.tool_plan.name,
            tool_arguments=state.tool_plan.arguments,
            metadata={
                "retrieval_count": len(state.context.retrieved_documents),
                "memory_count": len(state.context.memory_entries),
            },
        )
        tool_decision = await self._governance_service.evaluate(tool_governance_context)
        state.governance_decision = tool_decision
        state.context = state.context.with_governance_decision(tool_decision)
        if self._event_publisher is not None:
            await self._event_publisher.publish_runtime(
                context=state.context,
                event_name=RuntimeEventName.GOVERNANCE_CHECKED,
                stage=self.stage.value,
                metadata={"allowed": tool_decision.allowed, "requested_tool": state.tool_plan.name, "reason": tool_decision.reason},
            )
        if not tool_decision.allowed:
            state.response_text = self._blocked_response(tool_decision)
            state.provider_name = "governance"
            state.model_name = "policy-engine"
            state.context = state.context.with_blocked_response(state.response_text)
            return

        tool_response = await self._tool_execution_service.execute(
            state.session,
            ToolExecutionRequest(name=state.tool_plan.name, arguments=state.tool_plan.arguments),
        )
        state.tool_response = tool_response
        tool_response_text = json.dumps(tool_response.model_dump(mode="json"), ensure_ascii=True)
        state.context = state.context.with_tool_result(tool_response, response_text=tool_response_text)
        if self._event_publisher is not None:
            await self._event_publisher.publish_runtime(
                context=state.context,
                event_name=RuntimeEventName.TOOL_EXECUTED,
                stage=self.stage.value,
                metadata={"tool_name": tool_response.name, "status": tool_response.status, "duration_ms": tool_response.trace.duration_ms},
            )

    def _blocked_response(self, decision: GovernanceDecision) -> str:
        if decision.requires_approval:
            return "This request requires approval before execution."
        return "This request was blocked by governance policy."


class PromptAssemblyHandler(BasePipelineStageHandler):
    stage = PipelineStage.PROMPT_ASSEMBLY_PHASE

    def __init__(self, prompt_assembly_service: PromptAssemblyService, governance_service: GovernanceService, observability_service: ObservabilityService, event_publisher: EventPublisher | None = None) -> None:
        self._prompt_assembly_service = prompt_assembly_service
        self._governance_service = governance_service
        self._observability_service = observability_service
        self._event_publisher = event_publisher

    async def handle(self, state: PipelineExecutionState) -> None:
        assert state.context is not None
        if state.context.blocked_response_text is not None:
            state.context = state.context.with_runtime_attributes({"prompt_skipped": True})
            return
        prompt_context = GovernanceInterceptorContext(
            trace_id=state.context.trace_id,
            agent_name=state.context.agent_name,
            conversation_id=state.context.conversation_id,
            user_id=state.context.user_id,
            message=state.request.message,
            target=GovernanceTarget.PROMPT_GENERATION,
            phase=InterceptionPhase.PRE_EXECUTION,
            metadata={"pipeline_stage": self.stage.value},
        )
        prompt_decision = await self._governance_service.intercept_pre_execution(prompt_context)
        state.governance_decision = prompt_decision.governance_decision
        state.context = state.context.with_governance_decision(prompt_decision.governance_decision)
        if not prompt_decision.allowed:
            state.response_text = self._blocked_response(prompt_decision.governance_decision)
            state.provider_name = "governance"
            state.model_name = "policy-engine"
            state.context = state.context.with_blocked_response(state.response_text)
            return
        assert state.retrieval is not None and state.memory is not None
        async with self._observability_service.span(
            "prompt.assemble",
            kind=SpanKind.PROMPT_ASSEMBLY,
            component="orchestration",
            retrieval_count=len(state.retrieval.citations),
            memory_count=len(state.memory.relevant_memories),
        ):
            messages = self._prompt_assembly_service.build_messages(
                state.request.message,
                state.retrieval,
                state.memory,
                state.context.tool_response_text,
            )
        state.context = state.context.with_messages(messages)
        await self._governance_service.intercept_post_execution(
            prompt_context.with_phase(
                InterceptionPhase.POST_EXECUTION,
                metadata={"message_count": len(messages)},
            )
        )
        if self._event_publisher is not None:
            await self._event_publisher.publish_runtime(
                context=state.context,
                event_name=RuntimeEventName.PROMPT_ASSEMBLED,
                stage=self.stage.value,
                metadata={"message_count": len(messages)},
            )

    def _blocked_response(self, decision: GovernanceDecision) -> str:
        if decision.requires_approval:
            return "This request requires approval before execution."
        return "This request was blocked by governance policy."


class LLMGenerationHandler(BasePipelineStageHandler):
    stage = PipelineStage.LLM_GENERATION_PHASE

    def __init__(self, llm_provider: BaseLLMProvider, observability_service: ObservabilityService, event_publisher: EventPublisher | None = None) -> None:
        self._llm_provider = llm_provider
        self._observability_service = observability_service
        self._event_publisher = event_publisher

    async def handle(self, state: PipelineExecutionState) -> None:
        assert state.context is not None
        if state.context.blocked_response_text is not None:
            state.response_text = state.context.blocked_response_text
            state.provider_name = state.provider_name or "governance"
            state.model_name = state.model_name or "policy-engine"
            return

        if self._event_publisher is not None:
            await self._event_publisher.publish_runtime(
                context=state.context,
                event_name=RuntimeEventName.LLM_INVOKED,
                stage=self.stage.value,
                metadata={"provider": self._llm_provider.provider_name, "model": self._llm_provider.chat_model},
            )

        async with self._observability_service.span(
            "llm.generate",
            kind=SpanKind.LLM_EXECUTION,
            component="llm",
            provider=self._llm_provider.provider_name,
            model=self._llm_provider.chat_model,
            message_count=len(state.context.llm_messages),
            streaming=state.stream_callback is not None,
        ):
            if state.stream_callback is None:
                state.response_text = await self._llm_provider.generate(list(state.context.llm_messages))
            else:
                accumulated: list[str] = []
                async for token in self._llm_provider.generate_stream(list(state.context.llm_messages)):
                    accumulated.append(token)
                    await state.stream_callback(token)
                state.response_text = "".join(accumulated)
        state.provider_name = self._llm_provider.provider_name
        state.model_name = self._llm_provider.chat_model
        if self._event_publisher is not None:
            await self._event_publisher.publish_runtime(
                context=state.context,
                event_name=RuntimeEventName.RESPONSE_GENERATED,
                stage=self.stage.value,
                metadata={"provider": state.provider_name, "model": state.model_name, "response_length": len(state.response_text or "")},
            )


class ResponseSynthesisHandler(BasePipelineStageHandler):
    stage = PipelineStage.RESPONSE_SYNTHESIS_PHASE

    def __init__(self, lifecycle_service: OrchestrationLifecycleService, memory_service: MemoryService) -> None:
        self._lifecycle_service = lifecycle_service
        self._memory_service = memory_service

    async def handle(self, state: PipelineExecutionState) -> None:
        assert state.context is not None and state.context.conversation is not None and state.response_text is not None
        user_message = await self._lifecycle_service.store_message(
            state.session,
            conversation_id=state.context.conversation.id,
            role="user",
            content=state.request.message,
            citations=[],
            metadata_json={
                "orchestration_trace_id": state.context.trace_id,
                "agent_name": state.selected_agent,
                "pipeline_stage": self.stage.value,
            },
        )
        await self._memory_service.remember_user_message(
            state.session,
            conversation_id=state.context.conversation.id,
            message_index=user_message.message_index,
            content=state.request.message,
        )
        orchestration = self._build_orchestration(state)
        state.orchestration = orchestration
        state.context = state.context.with_orchestration(orchestration)
        await self._lifecycle_service.store_message(
            state.session,
            conversation_id=state.context.conversation.id,
            role="assistant",
            content=state.response_text,
            citations=list(state.context.citations),
            metadata_json={
                "orchestration_trace_id": state.context.trace_id,
                "tool_used": orchestration.tool_invocation.model_dump() if orchestration.tool_invocation else None,
                "agent_name": state.selected_agent,
                "pipeline_stage": self.stage.value,
            },
        )

    def _build_orchestration(self, state: PipelineExecutionState) -> OrchestrationMetadata:
        tool_invocation = None
        if state.tool_response is not None:
            tool_invocation = ToolInvocationSummary(
                name=state.tool_response.name,
                status=state.tool_response.status,
                trace_id=state.tool_response.trace.trace_id,
            )
        decision = state.governance_decision
        governance_summary = None
        if decision is not None:
            governance_summary = GovernanceSummary(
                allowed=decision.allowed,
                reason=decision.reason,
                requires_approval=decision.requires_approval,
                requested_tool=state.tool_plan.name if state.tool_plan else None,
                approval_status=decision.approval.status if decision.approval else None,
                audit_record_id=decision.audit_record.record_id if decision.audit_record else None,
                violations=list(decision.violations),
            )
        return OrchestrationMetadata(
            trace_id=state.context.trace_id,
            retrieval_count=len(state.context.retrieved_documents),
            memory_count=len(state.context.memory_entries),
            tool_invocation=tool_invocation,
            governance=governance_summary,
        )


class AuditHandler(BasePipelineStageHandler):
    stage = PipelineStage.AUDIT_PHASE

    def __init__(self, observability_service: ObservabilityService) -> None:
        self._observability_service = observability_service

    async def handle(self, state: PipelineExecutionState) -> None:
        assert state.context is not None
        self._observability_service.log_info(
            "pipeline_execution_audited",
            trace_id=state.context.trace_id,
            conversation_id=state.context.conversation_id,
            agent_name=state.selected_agent or state.context.agent_name,
            stage_count=len(state.context.state.steps),
            pipeline_stage=self.stage.value,
        )


class ResponseCompletedHandler(BasePipelineStageHandler):
    stage = PipelineStage.RESPONSE_COMPLETED

    def __init__(self, lifecycle_service: OrchestrationLifecycleService, governance_service: GovernanceService, event_publisher: EventPublisher | None = None) -> None:
        self._lifecycle_service = lifecycle_service
        self._governance_service = governance_service
        self._event_publisher = event_publisher

    async def handle(self, state: PipelineExecutionState) -> None:
        await self._lifecycle_service.commit_turn(state.session)
        if state.context is not None:
            await self._governance_service.intercept_post_execution(
                GovernanceInterceptorContext(
                    trace_id=state.context.trace_id,
                    agent_name=state.context.agent_name,
                    conversation_id=state.context.conversation_id,
                    user_id=state.context.user_id,
                    message=state.request.message,
                    target=GovernanceTarget.WORKFLOW_EXECUTION,
                    phase=InterceptionPhase.POST_EXECUTION,
                    workflow_name="chat-turn",
                    metadata={"pipeline_stage": self.stage.value, "provider": state.provider_name, "model": state.model_name},
                )
            )
        if self._event_publisher is not None and state.context is not None:
            await self._event_publisher.publish_runtime(
                context=state.context,
                event_name=RuntimeEventName.EXECUTION_COMPLETED,
                stage=self.stage.value,
                metadata={"provider": state.provider_name, "model": state.model_name},
            )
