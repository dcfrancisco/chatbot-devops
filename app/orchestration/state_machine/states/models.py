from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RuntimeLifecycleState(StrEnum):
    INITIALIZED = "initialized"
    REQUEST_RECEIVED = "initialized"

    CONTEXT_READY = "context_ready"
    CONTEXT_INITIALIZED = "context_ready"

    RETRIEVING = "retrieving"
    RETRIEVAL_PHASE = "retrieving"

    GOVERNANCE_CHECK = "governance_check"
    GOVERNANCE_PHASE = "governance_check"

    AGENT_SELECTED = "agent_selected"
    AGENT_SELECTION_PHASE = "agent_selected"
    TOOL_DECISION_PHASE = "agent_selected"

    TOOL_EXECUTING = "tool_executing"
    TOOL_EXECUTION_PHASE = "tool_executing"

    PROMPT_BUILDING = "prompt_building"
    PROMPT_ASSEMBLY_PHASE = "prompt_building"

    LLM_GENERATING = "llm_generating"
    LLM_GENERATION_PHASE = "llm_generating"

    RESPONSE_SYNTHESIZING = "response_synthesizing"
    RESPONSE_SYNTHESIS_PHASE = "response_synthesizing"
    AUDIT_PHASE = "response_synthesizing"

    COMPLETED = "completed"
    RESPONSE_COMPLETED = "completed"

    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "failed"


ExecutionStage = RuntimeLifecycleState


@dataclass(slots=True, frozen=True)
class ToolPlan:
    name: str
    arguments: dict[str, object]


@dataclass(slots=True, frozen=True)
class ExecutionStep:
    name: str
    stage: RuntimeLifecycleState
    status: str = "completed"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class StateTransitionTrace:
    from_state: RuntimeLifecycleState
    to_state: RuntimeLifecycleState
    step_name: str
    status: str
    occurred_at: datetime = field(default_factory=_utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


@dataclass(slots=True, frozen=True)
class WorkflowState:
    workflow_id: str | None = None
    status: str = "idle"
    current_step: str | None = None
    completed_steps: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ExecutionState:
    stage: RuntimeLifecycleState = RuntimeLifecycleState.INITIALIZED
    route_name: str = "deterministic"
    selected_tool: str | None = None
    workflow: WorkflowState = field(default_factory=WorkflowState)
    steps: tuple[ExecutionStep, ...] = ()
    transition_trace: tuple[StateTransitionTrace, ...] = ()

    @property
    def current_state(self) -> RuntimeLifecycleState:
        return self.stage
