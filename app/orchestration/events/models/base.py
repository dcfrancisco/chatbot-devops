from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class RuntimeEventName(StrEnum):
    REQUEST_STARTED = "RequestStarted"
    RETRIEVAL_STARTED = "RetrievalStarted"
    RETRIEVAL_COMPLETED = "RetrievalCompleted"
    AGENT_SELECTED = "AgentSelected"
    TOOL_REQUESTED = "ToolRequested"
    TOOL_EXECUTED = "ToolExecuted"
    GOVERNANCE_CHECKED = "GovernanceChecked"
    PROMPT_ASSEMBLED = "PromptAssembled"
    LLM_INVOKED = "LLMInvoked"
    RESPONSE_GENERATED = "ResponseGenerated"
    EXECUTION_COMPLETED = "ExecutionCompleted"
    EXECUTION_FAILED = "ExecutionFailed"
    STAGE_STARTED = "StageStarted"
    STAGE_COMPLETED = "StageCompleted"
    STATE_TRANSITIONED = "StateTransitioned"
    TRACE_RECORDED = "TraceRecorded"
    WORKFLOW_STARTED = "WorkflowStarted"
    WORKFLOW_STEP_STARTED = "WorkflowStepStarted"
    WORKFLOW_STEP_RETRIED = "WorkflowStepRetried"
    WORKFLOW_STEP_COMPLETED = "WorkflowStepCompleted"
    WORKFLOW_AWAITING_APPROVAL = "WorkflowAwaitingApproval"
    WORKFLOW_CANCELLED = "WorkflowCancelled"
    WORKFLOW_COMPLETED = "WorkflowCompleted"
    WORKFLOW_FAILED = "WorkflowFailed"


@dataclass(slots=True, frozen=True)
class EventCorrelation:
    request_id: str
    trace_id: str
    correlation_id: str | None = None
    conversation_id: str | None = None
    user_id: str | None = None


@dataclass(slots=True, frozen=True)
class ExecutionEvent:
    event_id: str
    event_name: RuntimeEventName
    event_type: str
    occurred_at: datetime
    correlation: EventCorrelation
    stage: str | None = None
    publisher: str = "runtime"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        event_name: RuntimeEventName,
        event_type: str,
        correlation: EventCorrelation,
        stage: str | None = None,
        publisher: str = "runtime",
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionEvent:
        return cls(
            event_id=str(uuid4()),
            event_name=event_name,
            event_type=event_type,
            occurred_at=datetime.now(timezone.utc),
            correlation=correlation,
            stage=stage,
            publisher=publisher,
            metadata=metadata or {},
        )
