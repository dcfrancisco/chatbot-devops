from dataclasses import replace
from typing import Any

from app.orchestration.state_machine.runtime import RuntimeStateMachine
from app.orchestration.state_machine.states import ExecutionStage, ExecutionState, ExecutionStep, ToolPlan, WorkflowState


_runtime_state_machine = RuntimeStateMachine()


def _workflow_evolve(
    self: WorkflowState,
    *,
    status: str | None = None,
    current_step: str | None = None,
    append_completed_step: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> WorkflowState:
    completed_steps = self.completed_steps
    if append_completed_step is not None:
        completed_steps = (*completed_steps, append_completed_step)
    return replace(
        self,
        status=status or self.status,
        current_step=current_step,
        completed_steps=completed_steps,
        metadata=metadata or self.metadata,
    )


def _execution_transition(
    self: ExecutionState,
    stage: ExecutionStage,
    *,
    step_name: str,
    status: str = "completed",
    metadata: dict[str, Any] | None = None,
    selected_tool: str | None = None,
    workflow: WorkflowState | None = None,
) -> ExecutionState:
    return _runtime_state_machine.transition(
        self,
        stage,
        step_name=step_name,
        status=status,
        metadata=metadata,
        selected_tool=selected_tool,
        workflow=workflow,
        error_message=str(metadata.get("reason")) if metadata and "reason" in metadata else None,
    )


def _execution_fail(self: ExecutionState, *, step_name: str, reason: str, metadata: dict[str, Any] | None = None) -> ExecutionState:
    return _runtime_state_machine.fail(self, step_name=step_name, reason=reason, metadata=metadata)


def _execution_cancel(self: ExecutionState, *, step_name: str, reason: str, metadata: dict[str, Any] | None = None) -> ExecutionState:
    return _runtime_state_machine.cancel(self, step_name=step_name, reason=reason, metadata=metadata)


def _execution_recover(
    self: ExecutionState,
    *,
    stage: ExecutionStage = ExecutionStage.CONTEXT_READY,
    step_name: str = "execution_recovered",
    metadata: dict[str, Any] | None = None,
) -> ExecutionState:
    return _runtime_state_machine.recover(self, next_state=stage, step_name=step_name, metadata=metadata)


WorkflowState.evolve = _workflow_evolve
ExecutionState.transition = _execution_transition
ExecutionState.fail = _execution_fail
ExecutionState.cancel = _execution_cancel
ExecutionState.recover = _execution_recover

__all__ = ["ExecutionStage", "ExecutionState", "ExecutionStep", "ToolPlan", "WorkflowState"]
