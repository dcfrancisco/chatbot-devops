from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field, replace
from typing import Any, Iterator

from app.db.models import Conversation, MemoryEntry
from app.governance.base import GovernanceContext, GovernanceDecision
from app.memory.models import MemoryContext
from app.models.api import Citation, OrchestrationMetadata, ToolExecutionResponse
from app.models.llm import LLMMessage
from app.observability.tracing.models import ExecutionTraceSpan
from app.orchestration.context.execution_metadata import ExecutionTraceRecord, GovernanceRecord, RuntimeMetadata, TimingMetadata, ToolResultRecord
from app.orchestration.context.execution_state import ExecutionStage, ExecutionState, WorkflowState
from app.rag.retriever import RetrievalResult


_execution_context_var: ContextVar[ExecutionContext | None] = ContextVar("execution_context", default=None)


@dataclass(slots=True, frozen=True)
class ExecutionContext:
    request_id: str
    conversation_id: str | None
    user_id: str | None
    trace_id: str
    runtime_metadata: RuntimeMetadata
    timing: TimingMetadata = field(default_factory=TimingMetadata)
    state: ExecutionState = field(default_factory=ExecutionState)
    workflow_state: WorkflowState = field(default_factory=WorkflowState)
    conversation: Conversation | None = None
    request_message: str = ""
    retrieved_documents: tuple[Citation, ...] = ()
    retrieval: RetrievalResult | None = None
    memory_entries: tuple[MemoryEntry, ...] = ()
    memory: MemoryContext | None = None
    tool_results: tuple[ToolResultRecord, ...] = ()
    governance_decisions: tuple[GovernanceRecord, ...] = ()
    execution_trace: ExecutionTraceRecord | None = None
    llm_messages: tuple[LLMMessage, ...] = ()
    orchestration: OrchestrationMetadata | None = None
    blocked_response_text: str | None = None
    tool_response_text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def agent_name(self) -> str:
        return self.runtime_metadata.agent_name

    @property
    def route_name(self) -> str:
        return self.state.route_name

    @property
    def current_stage(self) -> ExecutionStage:
        return self.state.stage

    @property
    def citations(self) -> tuple[Citation, ...]:
        return self.retrieved_documents

    def with_conversation(self, conversation: Conversation) -> ExecutionContext:
        return replace(self, conversation_id=conversation.id, conversation=conversation, timing=self.timing.touch())

    def transition(
        self,
        stage: ExecutionStage,
        *,
        step_name: str,
        status: str = "completed",
        metadata: dict[str, Any] | None = None,
        selected_tool: str | None = None,
        workflow_state: WorkflowState | None = None,
    ) -> ExecutionContext:
        next_workflow_state = workflow_state or self.workflow_state
        next_state = self.state.transition(
            stage,
            step_name=step_name,
            status=status,
            metadata=metadata,
            selected_tool=selected_tool,
            workflow=next_workflow_state,
        )
        return replace(self, state=next_state, workflow_state=next_workflow_state, timing=self.timing.touch())

    def with_retrieval(self, retrieval: RetrievalResult) -> ExecutionContext:
        return replace(
            self,
            retrieval=retrieval,
            retrieved_documents=tuple(retrieval.citations),
            timing=self.timing.touch(),
        )

    def with_memory(self, memory: MemoryContext) -> ExecutionContext:
        return replace(
            self,
            memory=memory,
            memory_entries=tuple(memory.relevant_memories),
            timing=self.timing.touch(),
        )

    def with_governance_decision(self, decision: GovernanceDecision) -> ExecutionContext:
        return replace(
            self,
            governance_decisions=(*self.governance_decisions, GovernanceRecord(decision=decision)),
            timing=self.timing.touch(),
        )

    def with_tool_result(self, response: ToolExecutionResponse, *, response_text: str | None = None) -> ExecutionContext:
        return replace(
            self,
            tool_results=(*self.tool_results, ToolResultRecord(response=response)),
            tool_response_text=response_text or self.tool_response_text,
            timing=self.timing.touch(),
        )

    def with_messages(self, messages: list[LLMMessage]) -> ExecutionContext:
        return replace(self, llm_messages=tuple(messages), timing=self.timing.touch())

    def with_orchestration(self, orchestration: OrchestrationMetadata) -> ExecutionContext:
        return replace(self, orchestration=orchestration, timing=self.timing.touch())

    def with_blocked_response(self, response_text: str) -> ExecutionContext:
        return replace(self, blocked_response_text=response_text, timing=self.timing.touch())

    def with_trace_span(self, span: ExecutionTraceSpan) -> ExecutionContext:
        record = self.execution_trace or ExecutionTraceRecord(
            trace_id=span.trace_id,
            correlation_id=span.correlation_id,
        )
        return replace(self, execution_trace=record.append_span(span), timing=self.timing.touch())

    def with_runtime_attributes(self, attributes: dict[str, Any]) -> ExecutionContext:
        runtime_metadata = self.runtime_metadata.merge_attributes(attributes)
        trace_record = self.execution_trace.merge_attributes(attributes) if self.execution_trace else None
        return replace(self, runtime_metadata=runtime_metadata, execution_trace=trace_record, timing=self.timing.touch())

    def with_workflow_state(self, workflow_state: WorkflowState) -> ExecutionContext:
        return replace(self, workflow_state=workflow_state, state=replace(self.state, workflow=workflow_state), timing=self.timing.touch())

    def with_metadata(self, metadata: dict[str, Any]) -> ExecutionContext:
        return replace(self, metadata={**self.metadata, **metadata}, timing=self.timing.touch())

    def complete(self, *, stage: ExecutionStage = ExecutionStage.COMPLETED) -> ExecutionContext:
        next_context = self.transition(stage, step_name="execution_completed")
        return replace(next_context, timing=next_context.timing.complete())

    def fail(self, *, reason: str) -> ExecutionContext:
        failed = self.state.fail(step_name="execution_failed", reason=reason)
        return replace(self, state=failed, timing=self.timing.complete())

    def cancel(self, *, reason: str) -> ExecutionContext:
        cancelled = self.state.cancel(step_name="execution_cancelled", reason=reason)
        return replace(self, state=cancelled, timing=self.timing.complete())

    def recover(self, *, stage: ExecutionStage = ExecutionStage.CONTEXT_READY, metadata: dict[str, Any] | None = None) -> ExecutionContext:
        recovered = self.state.recover(stage=stage, metadata=metadata)
        return replace(self, state=recovered, timing=self.timing.touch())

    def to_governance_context(self, *, requested_tool: str | None, tool_arguments: dict[str, Any], metadata: dict[str, Any] | None = None) -> GovernanceContext:
        return GovernanceContext(
            trace_id=self.trace_id,
            agent_name=self.agent_name,
            conversation_id=self.conversation_id,
            message=self.request_message,
            requested_tool=requested_tool,
            tool_arguments=tool_arguments,
            metadata={**self.runtime_metadata.attributes, **(metadata or {})},
        )


def get_current_execution_context() -> ExecutionContext | None:
    return _execution_context_var.get()


def set_current_execution_context(context: ExecutionContext | None) -> Token[ExecutionContext | None]:
    return _execution_context_var.set(context)


def reset_current_execution_context(token: Token[ExecutionContext | None]) -> None:
    _execution_context_var.reset(token)


@contextmanager
def bind_execution_context(context: ExecutionContext) -> Iterator[ExecutionContext]:
    token = set_current_execution_context(context)
    try:
        yield context
    finally:
        reset_current_execution_context(token)
