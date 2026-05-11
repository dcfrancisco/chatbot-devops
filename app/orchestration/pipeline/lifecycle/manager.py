from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from app.observability.service import ObservabilityService
from app.orchestration.events import EventPublisher, RuntimeEventName
from app.observability.tracing.models import ExecutionTraceSpan, SpanKind
from app.orchestration.context import ExecutionStage, StateMachineTracer, bind_execution_context
from app.orchestration.pipeline.execution import PipelineExecutionState, PipelineStage
from app.orchestration.pipeline.stages import BasePipelineStageHandler


PIPELINE_STAGE_TO_EXECUTION_STAGE: dict[PipelineStage, ExecutionStage] = {
    PipelineStage.REQUEST_RECEIVED: ExecutionStage.REQUEST_RECEIVED,
    PipelineStage.CONTEXT_INITIALIZED: ExecutionStage.CONTEXT_INITIALIZED,
    PipelineStage.RETRIEVAL_PHASE: ExecutionStage.RETRIEVAL_PHASE,
    PipelineStage.GOVERNANCE_PHASE: ExecutionStage.GOVERNANCE_PHASE,
    PipelineStage.AGENT_SELECTION_PHASE: ExecutionStage.AGENT_SELECTION_PHASE,
    PipelineStage.TOOL_DECISION_PHASE: ExecutionStage.TOOL_DECISION_PHASE,
    PipelineStage.TOOL_EXECUTION_PHASE: ExecutionStage.TOOL_EXECUTION_PHASE,
    PipelineStage.PROMPT_ASSEMBLY_PHASE: ExecutionStage.PROMPT_ASSEMBLY_PHASE,
    PipelineStage.LLM_GENERATION_PHASE: ExecutionStage.LLM_GENERATION_PHASE,
    PipelineStage.RESPONSE_SYNTHESIS_PHASE: ExecutionStage.RESPONSE_SYNTHESIS_PHASE,
    PipelineStage.AUDIT_PHASE: ExecutionStage.AUDIT_PHASE,
    PipelineStage.RESPONSE_COMPLETED: ExecutionStage.RESPONSE_COMPLETED,
}


@dataclass(slots=True)
class PipelineLifecycleManager:
    observability_service: ObservabilityService
    event_publisher: EventPublisher | None = None
    state_machine_tracer: StateMachineTracer = StateMachineTracer()

    async def run_stage(self, handler: BasePipelineStageHandler, state: PipelineExecutionState) -> None:
        if asyncio.current_task() is not None and asyncio.current_task().cancelled():
            raise asyncio.CancelledError()

        started_at = datetime.now(timezone.utc)
        status = "completed"
        error_message: str | None = None

        try:
            if state.context is not None and self.event_publisher is not None:
                await self.event_publisher.publish_runtime(
                    context=state.context,
                    event_name=RuntimeEventName.STAGE_STARTED,
                    stage=handler.stage.value,
                    metadata={"stage": handler.stage.value},
                )
            if state.context is None:
                await handler.handle(state)
            else:
                with bind_execution_context(state.context):
                    async with self.observability_service.span(
                        f"pipeline.{handler.stage.value}",
                        kind=SpanKind.PIPELINE_STAGE,
                        component="orchestration",
                        stage=handler.stage.value,
                        conversation_id=state.context.conversation_id,
                    ):
                        await handler.handle(state)
        except asyncio.CancelledError:
            status = "cancelled"
            error_message = "execution_cancelled"
            if state.context is not None and self.event_publisher is not None:
                await self.event_publisher.publish_runtime(
                    context=state.context,
                    event_name=RuntimeEventName.EXECUTION_FAILED,
                    stage=handler.stage.value,
                    metadata={"status": status, "reason": error_message},
                )
            raise
        except Exception as exc:
            status = "failed"
            error_message = str(exc)
            if state.context is not None and self.event_publisher is not None:
                await self.event_publisher.publish_runtime(
                    context=state.context,
                    event_name=RuntimeEventName.EXECUTION_FAILED,
                    stage=handler.stage.value,
                    metadata={"status": status, "reason": error_message},
                )
            raise
        finally:
            ended_at = datetime.now(timezone.utc)
            if state.context is not None:
                previous_transition_count = len(state.context.state.transition_trace)
                state.context = self._record_stage_timing(
                    state=state,
                    stage=handler.stage,
                    status=status,
                    started_at=started_at,
                    ended_at=ended_at,
                    error_message=error_message,
                )
                if self.event_publisher is not None and len(state.context.state.transition_trace) > previous_transition_count:
                    transition = state.context.state.transition_trace[-1]
                    await self.event_publisher.publish_runtime(
                        context=state.context,
                        event_name=RuntimeEventName.STATE_TRANSITIONED,
                        stage=handler.stage.value,
                        metadata={
                            "from_state": transition.from_state.name,
                            "to_state": transition.to_state.name,
                            "step_name": transition.step_name,
                            "status": transition.status,
                        },
                    )
                if status == "completed" and self.event_publisher is not None:
                    await self.event_publisher.publish_runtime(
                        context=state.context,
                        event_name=RuntimeEventName.STAGE_COMPLETED,
                        stage=handler.stage.value,
                        metadata={"status": status, "stage": handler.stage.value},
                    )
                    await self.event_publisher.publish_trace(
                        context=state.context,
                        event_name=RuntimeEventName.TRACE_RECORDED,
                        stage=handler.stage.value,
                        metadata={"status": status, "stage": handler.stage.value},
                    )

    def _record_stage_timing(
        self,
        *,
        state: PipelineExecutionState,
        stage: PipelineStage,
        status: str,
        started_at: datetime,
        ended_at: datetime,
        error_message: str | None,
    ):
        assert state.context is not None
        duration_ms = int((ended_at - started_at).total_seconds() * 1000)
        timings = dict(state.context.metadata.get("pipeline_stage_timings", {}))
        timings[stage.value] = {
            "status": status,
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
            "duration_ms": duration_ms,
            "error": error_message,
        }
        span = ExecutionTraceSpan.create(
            trace_id=state.context.trace_id,
            span_id=f"pipeline:{stage.value}",
            name=f"pipeline.{stage.value}",
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            correlation_id=state.context.runtime_metadata.correlation_id,
            parent_span_id=None,
            kind=SpanKind.PIPELINE_STAGE,
            component="orchestration",
            attributes={"stage": stage.value, "duration_ms": duration_ms},
        )
        context = state.context.with_trace_span(span).with_metadata(
            {
                "pipeline_stage_timings": timings,
                "current_pipeline_stage": stage.value,
            }
        )
        if status == "failed":
            failed_context = context.fail(reason=error_message or f"pipeline_stage_failed:{stage.value}")
            return failed_context.with_metadata(self.state_machine_tracer.as_metadata(failed_context.state))
        if status == "cancelled":
            cancelled_context = context.cancel(reason="execution_cancelled")
            return cancelled_context.with_metadata(self.state_machine_tracer.as_metadata(cancelled_context.state))
        execution_stage = PIPELINE_STAGE_TO_EXECUTION_STAGE[stage]
        if context.current_stage == execution_stage:
            return context.with_metadata(self.state_machine_tracer.as_metadata(context.state))
        transitioned = context.transition(execution_stage, step_name=stage.value)
        return transitioned.with_metadata(self.state_machine_tracer.as_metadata(transitioned.state))
