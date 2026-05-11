from __future__ import annotations

from app.orchestration.events.bus import EventBus
from app.orchestration.events.models import EventCorrelation, RuntimeEventName
from app.workflows.events.models import WorkflowEvent
from app.workflows.state import WorkflowRunState


class WorkflowEventPublisher:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    async def publish_runtime(
        self,
        *,
        state: WorkflowRunState,
        event_name: RuntimeEventName,
        stage: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        event = WorkflowEvent.create(
            event_name=event_name,
            correlation=self._correlation(state),
            stage=stage,
            event_type="workflow",
            metadata=metadata,
        )
        await self._event_bus.publish(event.envelope)

    async def publish_trace(
        self,
        *,
        state: WorkflowRunState,
        event_name: RuntimeEventName,
        stage: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        event = WorkflowEvent.create(
            event_name=event_name,
            correlation=self._correlation(state),
            stage=stage,
            event_type="trace",
            metadata=metadata,
        )
        await self._event_bus.publish(event.envelope)

    def _correlation(self, state: WorkflowRunState) -> EventCorrelation:
        return EventCorrelation(
            request_id=state.request_id,
            trace_id=state.trace_id,
            correlation_id=state.correlation_id,
            conversation_id=state.conversation_id,
            user_id=state.user_id,
        )