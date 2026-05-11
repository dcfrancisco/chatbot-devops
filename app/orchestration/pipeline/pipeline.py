from __future__ import annotations

from collections.abc import Sequence

from app.orchestration.pipeline.execution import PipelineExecutionResult, PipelineExecutionState, TokenEmitter
from app.orchestration.pipeline.lifecycle import PipelineLifecycleManager
from app.orchestration.pipeline.stages import BasePipelineStageHandler


class ExecutionPipeline:
    """Stage-based orchestration pipeline.

    Example:

        state = await pipeline.run(session=session, request=request)
        response = state.to_chat_response()

    For streaming:

        async def emit(token: str) -> None:
            yield_buffer.append(token)

        result = await pipeline.run(session=session, request=request, stream_callback=emit)
    """

    def __init__(
        self,
        *,
        stages: Sequence[BasePipelineStageHandler],
        lifecycle_manager: PipelineLifecycleManager,
    ) -> None:
        self._stages = list(stages)
        self._lifecycle_manager = lifecycle_manager

    async def run(self, state: PipelineExecutionState, *, stream_callback: TokenEmitter | None = None) -> PipelineExecutionResult:
        state.stream_callback = stream_callback
        for handler in self._stages:
            await self._lifecycle_manager.run_stage(handler, state)

        context = state.context
        if context is None or state.response_text is None or state.provider_name is None or state.model_name is None or state.orchestration is None:
            raise RuntimeError("Execution pipeline completed without a full response payload")

        context = context.complete(stage=context.current_stage)
        state.context = context
        return PipelineExecutionResult(
            context=context,
            response_text=state.response_text,
            provider_name=state.provider_name,
            model_name=state.model_name,
            orchestration=state.orchestration,
        )
