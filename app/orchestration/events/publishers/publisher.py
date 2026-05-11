from __future__ import annotations

from app.orchestration.context import ExecutionContext
from app.orchestration.events.bus import EventBus
from app.orchestration.events.models import RuntimeEventName
from app.orchestration.events.tracing import EventFactory


class EventPublisher:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    async def publish_runtime(
        self,
        *,
        context: ExecutionContext,
        event_name: RuntimeEventName,
        stage: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        event = EventFactory.runtime_event(
            context=context,
            event_name=event_name,
            stage=stage,
            metadata=metadata,
        )
        await self._event_bus.publish(event.envelope)

    async def publish_trace(
        self,
        *,
        context: ExecutionContext,
        event_name: RuntimeEventName,
        stage: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        event = EventFactory.tracing_event(
            context=context,
            event_name=event_name,
            stage=stage,
            metadata=metadata,
        )
        await self._event_bus.publish(event.envelope)
