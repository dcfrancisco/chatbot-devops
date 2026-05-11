from app.orchestration.state_machine.states import RuntimeLifecycleState


STANDARD_RUNTIME_PATH: tuple[RuntimeLifecycleState, ...] = (
    RuntimeLifecycleState.INITIALIZED,
    RuntimeLifecycleState.CONTEXT_READY,
    RuntimeLifecycleState.RETRIEVING,
    RuntimeLifecycleState.GOVERNANCE_CHECK,
    RuntimeLifecycleState.AGENT_SELECTED,
    RuntimeLifecycleState.TOOL_EXECUTING,
    RuntimeLifecycleState.PROMPT_BUILDING,
    RuntimeLifecycleState.LLM_GENERATING,
    RuntimeLifecycleState.RESPONSE_SYNTHESIZING,
    RuntimeLifecycleState.COMPLETED,
)


FAILURE_RECOVERY_PATH: tuple[RuntimeLifecycleState, ...] = (
    RuntimeLifecycleState.INITIALIZED,
    RuntimeLifecycleState.CONTEXT_READY,
    RuntimeLifecycleState.RETRIEVING,
    RuntimeLifecycleState.FAILED,
    RuntimeLifecycleState.CONTEXT_READY,
)