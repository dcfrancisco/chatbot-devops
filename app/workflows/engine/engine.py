from __future__ import annotations

import asyncio
from uuid import uuid4

from app.observability.service import ObservabilityService
from app.orchestration.context import ExecutionContext
from app.orchestration.events.models import RuntimeEventName
from app.workflows.definitions import WorkflowDefinition
from app.workflows.events import WorkflowEventPublisher
from app.workflows.execution import StepHandlerRegistry, WorkflowCancellationToken, WorkflowExecutionContext, WorkflowRunResult, WorkflowStateListener
from app.workflows.state import WorkflowRunState, WorkflowStatus, WorkflowStepStatus


class WorkflowEngine:
    def __init__(
        self,
        handler_registry: StepHandlerRegistry,
        observability_service: ObservabilityService,
        event_publisher: WorkflowEventPublisher | None = None,
    ) -> None:
        self._handler_registry = handler_registry
        self._observability_service = observability_service
        self._event_publisher = event_publisher

    async def execute(
        self,
        *,
        definition: WorkflowDefinition,
        input_data: dict[str, object],
        services: dict[str, object] | None = None,
        execution_context: ExecutionContext | None = None,
        session=None,
        cancellation_token: WorkflowCancellationToken | None = None,
        state_listener: WorkflowStateListener | None = None,
        run_id: str | None = None,
    ) -> WorkflowRunResult:
        trace_id = execution_context.trace_id if execution_context is not None else self._observability_service.current_trace_id() or str(uuid4())
        request_id = execution_context.request_id if execution_context is not None else run_id or str(uuid4())
        correlation_id = execution_context.runtime_metadata.correlation_id if execution_context is not None else self._observability_service.current_correlation_id()

        state = WorkflowRunState.create(
            workflow_name=definition.name,
            workflow_version=definition.version,
            trace_id=trace_id,
            request_id=request_id,
            correlation_id=correlation_id,
            conversation_id=execution_context.conversation_id if execution_context is not None else None,
            user_id=execution_context.user_id if execution_context is not None else None,
            input_data=dict(input_data),
            run_id=run_id,
            metadata=definition.metadata_payload(),
        ).start()
        context = WorkflowExecutionContext(
            definition=definition,
            run_id=state.run_id,
            trace_id=trace_id,
            input_data=dict(input_data),
            services=dict(services or {}),
            session=session,
            execution_context=execution_context,
            cancellation_token=cancellation_token or WorkflowCancellationToken(),
        )
        context.set_run_state(state)
        await self._notify_state(state_listener, state)
        await self._publish_runtime(state=state, event_name=RuntimeEventName.WORKFLOW_STARTED, metadata={"workflow_name": definition.name})

        current_step = definition.entry_step
        executed_steps = 0
        safety_limit = max(4, len(definition.steps) * 4)

        async with self._observability_service.trace_scope(
            root_name=f"workflow.{definition.name}",
            trace_id=trace_id,
            correlation_id=correlation_id,
            attributes={"workflow_name": definition.name, "workflow_run_id": state.run_id},
        ):
            while current_step is not None:
                if executed_steps >= safety_limit:
                    state = state.fail(reason=f"workflow_safety_limit_exceeded:{definition.name}")
                    context.set_run_state(state)
                    await self._notify_state(state_listener, state)
                    await self._publish_runtime(state=state, event_name=RuntimeEventName.WORKFLOW_FAILED, metadata={"reason": state.failure_reason})
                    return WorkflowRunResult(state=state, output=state.output)

                step = definition.get_step(current_step)
                if context.cancellation_token.cancelled:
                    state = state.cancel(step_name=current_step, reason=context.cancellation_token.reason or "workflow_cancelled")
                    context.set_run_state(state)
                    await self._notify_state(state_listener, state)
                    await self._publish_runtime(state=state, event_name=RuntimeEventName.WORKFLOW_CANCELLED, metadata={"reason": state.cancellation_reason})
                    return WorkflowRunResult(state=state, output=state.output)

                handler = self._handler_registry.get(step.handler)
                step_input = context.snapshot()
                state = state.start_step(step_name=step.name, handler=step.handler, input_snapshot=step_input, metadata={"description": step.description})
                context.set_run_state(state)
                await self._notify_state(state_listener, state)
                await self._publish_runtime(state=state, event_name=RuntimeEventName.WORKFLOW_STEP_STARTED, stage=step.name, metadata={"handler": step.handler})

                outcome = None
                attempts = step.retry_policy.normalized_attempts()
                for attempt in range(1, attempts + 1):
                    if context.cancellation_token.cancelled:
                        state = state.cancel(step_name=step.name, reason=context.cancellation_token.reason or "workflow_cancelled")
                        context.set_run_state(state)
                        await self._notify_state(state_listener, state)
                        await self._publish_runtime(state=state, event_name=RuntimeEventName.WORKFLOW_CANCELLED, stage=step.name, metadata={"reason": state.cancellation_reason})
                        return WorkflowRunResult(state=state, output=state.output)

                    try:
                        async with self._observability_service.span(
                            f"workflow.step.{step.name}",
                            workflow_name=definition.name,
                            workflow_run_id=state.run_id,
                            step_name=step.name,
                            handler=step.handler,
                            attempt=attempt,
                        ):
                            outcome = await handler.handle(context, step)
                        break
                    except Exception as exc:
                        if attempt < attempts:
                            state = state.retry_step(
                                step_name=step.name,
                                error_message=str(exc),
                                metadata={"attempt": attempt, "max_attempts": attempts},
                            )
                            context.set_run_state(state)
                            await self._notify_state(state_listener, state)
                            await self._publish_runtime(
                                state=state,
                                event_name=RuntimeEventName.WORKFLOW_STEP_RETRIED,
                                stage=step.name,
                                metadata={"attempt": attempt, "error": str(exc)},
                            )
                            if step.retry_policy.backoff_seconds > 0:
                                await asyncio.sleep(step.retry_policy.backoff_seconds)
                            continue

                        state = state.fail_step(step_name=step.name, error_message=str(exc), metadata={"attempts": attempt})
                        context.set_run_state(state)
                        await self._notify_state(state_listener, state)
                        await self._publish_runtime(state=state, event_name=RuntimeEventName.WORKFLOW_FAILED, stage=step.name, metadata={"reason": str(exc)})
                        return WorkflowRunResult(state=state, output=state.output)

                assert outcome is not None
                executed_steps += 1

                if outcome.status == WorkflowStepStatus.AWAITING_APPROVAL:
                    state = state.await_approval(step_name=step.name, metadata=outcome.metadata)
                    context.set_run_state(state)
                    context.merge_output(outcome.output)
                    await self._notify_state(state_listener, state)
                    await self._publish_runtime(state=state, event_name=RuntimeEventName.WORKFLOW_AWAITING_APPROVAL, stage=step.name, metadata=outcome.metadata)
                    return WorkflowRunResult(state=state, output={**state.output, **outcome.output})

                if outcome.status == WorkflowStepStatus.CANCELLED:
                    reason = str(outcome.metadata.get("reason") or "workflow_cancelled")
                    state = state.cancel(step_name=step.name, reason=reason)
                    context.set_run_state(state)
                    await self._notify_state(state_listener, state)
                    await self._publish_runtime(state=state, event_name=RuntimeEventName.WORKFLOW_CANCELLED, stage=step.name, metadata={"reason": reason})
                    return WorkflowRunResult(state=state, output=state.output)

                if outcome.status == WorkflowStepStatus.FAILED:
                    next_failed_step = outcome.next_step or definition.next_step(step.name, outcome.status.value)
                    state = state.fail_step(step_name=step.name, error_message=str(outcome.metadata.get("reason") or "workflow_step_failed"), metadata=outcome.metadata)
                    context.set_run_state(state)
                    await self._notify_state(state_listener, state)
                    if next_failed_step is None:
                        await self._publish_runtime(state=state, event_name=RuntimeEventName.WORKFLOW_FAILED, stage=step.name, metadata=outcome.metadata)
                        return WorkflowRunResult(state=state, output=state.output)
                    current_step = next_failed_step
                    continue

                state = state.complete_step(step_name=step.name, output=outcome.output, metadata=outcome.metadata)
                context.merge_output(outcome.output)
                context.set_run_state(state)
                await self._notify_state(state_listener, state)
                await self._publish_runtime(state=state, event_name=RuntimeEventName.WORKFLOW_STEP_COMPLETED, stage=step.name, metadata=outcome.metadata)
                await self._publish_trace(state=state, event_name=RuntimeEventName.WORKFLOW_STEP_COMPLETED, stage=step.name, metadata={"step": step.name})

                current_step = outcome.next_step or definition.next_step(step.name, outcome.status.value)

            final_state = state.complete(output=context.variables)
            context.set_run_state(final_state)
            await self._notify_state(state_listener, final_state)
            await self._publish_runtime(state=final_state, event_name=RuntimeEventName.WORKFLOW_COMPLETED, metadata={"workflow_name": definition.name})
            return WorkflowRunResult(state=final_state, output=final_state.output)

    async def _notify_state(self, listener: WorkflowStateListener | None, state: WorkflowRunState) -> None:
        self._observability_service.increment(
            "workflows.state.transition",
            workflow_name=state.workflow_name,
            workflow_status=state.status,
            current_step=state.current_step or "none",
        )
        self._observability_service.log_info(
            "workflow_state_updated",
            workflow_name=state.workflow_name,
            workflow_run_id=state.run_id,
            workflow_status=state.status,
            current_step=state.current_step,
            trace_id=state.trace_id,
        )
        if listener is None:
            return
        result = listener(state)
        if asyncio.iscoroutine(result):
            await result

    async def _publish_runtime(self, *, state: WorkflowRunState, event_name: RuntimeEventName, stage: str | None = None, metadata: dict[str, object] | None = None) -> None:
        if self._event_publisher is None:
            return
        await self._event_publisher.publish_runtime(state=state, event_name=event_name, stage=stage, metadata=metadata)

    async def _publish_trace(self, *, state: WorkflowRunState, event_name: RuntimeEventName, stage: str | None = None, metadata: dict[str, object] | None = None) -> None:
        if self._event_publisher is None:
            return
        await self._event_publisher.publish_trace(state=state, event_name=event_name, stage=stage, metadata=metadata)