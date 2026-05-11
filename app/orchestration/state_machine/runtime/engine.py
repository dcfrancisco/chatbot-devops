from __future__ import annotations

from dataclasses import replace

from app.orchestration.state_machine.states import ExecutionState, ExecutionStep, RuntimeLifecycleState, StateTransitionTrace, WorkflowState
from app.orchestration.state_machine.transitions import RuntimeStateTransition
from app.orchestration.state_machine.validators import TransitionValidator


class RuntimeStateMachine:
    def __init__(self, validator: TransitionValidator | None = None) -> None:
        self._validator = validator or TransitionValidator()

    def transition(
        self,
        state: ExecutionState,
        next_state: RuntimeLifecycleState,
        *,
        step_name: str,
        status: str = "completed",
        metadata: dict[str, object] | None = None,
        selected_tool: str | None = None,
        workflow: WorkflowState | None = None,
        error_message: str | None = None,
    ) -> ExecutionState:
        transition = RuntimeStateTransition(
            from_state=state.stage,
            to_state=next_state,
            step_name=step_name,
            status=status,
            metadata=dict(metadata or {}),
            error_message=error_message,
        )
        self._validator.validate(transition.from_state, transition.to_state)
        if transition.from_state == transition.to_state:
            return state

        step = ExecutionStep(
            name=step_name,
            stage=next_state,
            status=status,
            metadata=dict(metadata or {}),
        )
        trace = StateTransitionTrace(
            from_state=transition.from_state,
            to_state=transition.to_state,
            step_name=step_name,
            status=status,
            metadata=dict(metadata or {}),
            error_message=error_message,
        )
        return replace(
            state,
            stage=next_state,
            selected_tool=selected_tool if selected_tool is not None else state.selected_tool,
            workflow=workflow or state.workflow,
            steps=(*state.steps, step),
            transition_trace=(*state.transition_trace, trace),
        )

    def fail(self, state: ExecutionState, *, step_name: str, reason: str, metadata: dict[str, object] | None = None) -> ExecutionState:
        return self.transition(
            state,
            RuntimeLifecycleState.FAILED,
            step_name=step_name,
            status="failed",
            metadata={"reason": reason, **(metadata or {})},
            error_message=reason,
        )

    def cancel(self, state: ExecutionState, *, step_name: str, reason: str, metadata: dict[str, object] | None = None) -> ExecutionState:
        return self.transition(
            state,
            RuntimeLifecycleState.CANCELLED,
            step_name=step_name,
            status="cancelled",
            metadata={"reason": reason, **(metadata or {})},
            error_message=reason,
        )

    def recover(
        self,
        state: ExecutionState,
        *,
        next_state: RuntimeLifecycleState = RuntimeLifecycleState.CONTEXT_READY,
        step_name: str = "execution_recovered",
        metadata: dict[str, object] | None = None,
    ) -> ExecutionState:
        return self.transition(
            state,
            next_state,
            step_name=step_name,
            status="recovered",
            metadata=dict(metadata or {}),
        )