from __future__ import annotations

from app.observability.service import ObservabilityService
from app.orchestration.events.models import ExecutionEvent
from app.orchestration.events.subscribers.base import EventSubscriber


class TracingEventSubscriber(EventSubscriber):
    name = "tracing-event-subscriber"

    def __init__(self, observability_service: ObservabilityService) -> None:
        self._observability_service = observability_service

    def accepts(self, event: ExecutionEvent) -> bool:
        return event.event_type == "trace"

    async def handle(self, event: ExecutionEvent) -> None:
        self._observability_service.increment(
            "orchestration.events.trace",
            event_name=event.event_name,
            stage=event.stage or "none",
        )
