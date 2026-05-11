from __future__ import annotations

from app.orchestration.state_machine.states import RuntimeLifecycleState


class TransitionValidationError(ValueError):
    pass


DEFAULT_ALLOWED_TRANSITIONS: dict[RuntimeLifecycleState, frozenset[RuntimeLifecycleState]] = {
    RuntimeLifecycleState.INITIALIZED: frozenset({
        RuntimeLifecycleState.CONTEXT_READY,
        RuntimeLifecycleState.FAILED,
        RuntimeLifecycleState.CANCELLED,
    }),
    RuntimeLifecycleState.CONTEXT_READY: frozenset({
        RuntimeLifecycleState.RETRIEVING,
        RuntimeLifecycleState.GOVERNANCE_CHECK,
        RuntimeLifecycleState.FAILED,
        RuntimeLifecycleState.CANCELLED,
    }),
    RuntimeLifecycleState.RETRIEVING: frozenset({
        RuntimeLifecycleState.GOVERNANCE_CHECK,
        RuntimeLifecycleState.FAILED,
        RuntimeLifecycleState.CANCELLED,
    }),
    RuntimeLifecycleState.GOVERNANCE_CHECK: frozenset({
        RuntimeLifecycleState.AGENT_SELECTED,
        RuntimeLifecycleState.FAILED,
        RuntimeLifecycleState.CANCELLED,
    }),
    RuntimeLifecycleState.AGENT_SELECTED: frozenset({
        RuntimeLifecycleState.TOOL_EXECUTING,
        RuntimeLifecycleState.PROMPT_BUILDING,
        RuntimeLifecycleState.FAILED,
        RuntimeLifecycleState.CANCELLED,
    }),
    RuntimeLifecycleState.TOOL_EXECUTING: frozenset({
        RuntimeLifecycleState.PROMPT_BUILDING,
        RuntimeLifecycleState.FAILED,
        RuntimeLifecycleState.CANCELLED,
    }),
    RuntimeLifecycleState.PROMPT_BUILDING: frozenset({
        RuntimeLifecycleState.LLM_GENERATING,
        RuntimeLifecycleState.RESPONSE_SYNTHESIZING,
        RuntimeLifecycleState.FAILED,
        RuntimeLifecycleState.CANCELLED,
    }),
    RuntimeLifecycleState.LLM_GENERATING: frozenset({
        RuntimeLifecycleState.RESPONSE_SYNTHESIZING,
        RuntimeLifecycleState.FAILED,
        RuntimeLifecycleState.CANCELLED,
    }),
    RuntimeLifecycleState.RESPONSE_SYNTHESIZING: frozenset({
        RuntimeLifecycleState.COMPLETED,
        RuntimeLifecycleState.FAILED,
        RuntimeLifecycleState.CANCELLED,
    }),
    RuntimeLifecycleState.COMPLETED: frozenset(),
    RuntimeLifecycleState.FAILED: frozenset({RuntimeLifecycleState.CONTEXT_READY}),
    RuntimeLifecycleState.CANCELLED: frozenset({RuntimeLifecycleState.CONTEXT_READY}),
}


class TransitionValidator:
    def __init__(
        self,
        allowed_transitions: dict[RuntimeLifecycleState, frozenset[RuntimeLifecycleState]] | None = None,
    ) -> None:
        self._allowed_transitions = allowed_transitions or DEFAULT_ALLOWED_TRANSITIONS

    def validate(self, current_state: RuntimeLifecycleState, next_state: RuntimeLifecycleState) -> None:
        if current_state == next_state:
            return
        allowed = self._allowed_transitions.get(current_state, frozenset())
        if next_state not in allowed:
            raise TransitionValidationError(
                f"Invalid runtime state transition from {current_state.name} to {next_state.name}"
            )