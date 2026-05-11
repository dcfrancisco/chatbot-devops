from __future__ import annotations

from app.observability.logging.service import StructuredLoggingService
from app.orchestration.events.models import ExecutionEvent
from app.orchestration.events.subscribers.base import EventSubscriber


class StructuredLogEventSubscriber(EventSubscriber):
    name = "structured-log-subscriber"

    def __init__(self, logging_service: StructuredLoggingService) -> None:
        self._logging_service = logging_service

    async def handle(self, event: ExecutionEvent) -> None:
        self._logging_service.info(
            "runtime_event_published",
            event_id=event.event_id,
            event_name=event.event_name,
            event_type=event.event_type,
            stage=event.stage,
            trace_id=event.correlation.trace_id,
            correlation_id=event.correlation.correlation_id,
            request_id=event.correlation.request_id,
            conversation_id=event.correlation.conversation_id,
            metadata=event.metadata,
        )
