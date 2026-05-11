from __future__ import annotations

from app.orchestration.state_machine.states import ExecutionState, RuntimeLifecycleState
from app.orchestration.state_machine.tracing.models import StateMachineTraceSnapshot


class StateMachineTracer:
    def snapshot(self, state: ExecutionState) -> StateMachineTraceSnapshot:
        last_transition = None
        if state.transition_trace:
            trace = state.transition_trace[-1]
            last_transition = {
                "from_state": trace.from_state.name,
                "to_state": trace.to_state.name,
                "step_name": trace.step_name,
                "status": trace.status,
                "occurred_at": trace.occurred_at.isoformat(),
                "error_message": trace.error_message,
                "metadata": trace.metadata,
            }
        return StateMachineTraceSnapshot(
            current_state=state.stage.name,
            transition_count=len(state.transition_trace),
            last_transition=last_transition,
            recoverable=state.stage in {RuntimeLifecycleState.FAILED, RuntimeLifecycleState.CANCELLED},
            metadata={
                "selected_tool": state.selected_tool,
                "route_name": state.route_name,
            },
        )

    def as_metadata(self, state: ExecutionState) -> dict[str, object]:
        snapshot = self.snapshot(state)
        return {
            "runtime_state_machine": {
                "current_state": snapshot.current_state,
                "transition_count": snapshot.transition_count,
                "last_transition": snapshot.last_transition,
                "recoverable": snapshot.recoverable,
                "metadata": snapshot.metadata,
            }
        }