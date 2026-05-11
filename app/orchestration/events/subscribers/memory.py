from __future__ import annotations

from dataclasses import dataclass, field

from app.orchestration.events.models import ExecutionEvent
from app.orchestration.events.subscribers.base import EventSubscriber


@dataclass(slots=True)
class InMemoryEventSubscriber(EventSubscriber):
    name: str = "in-memory-subscriber"
    events: list[ExecutionEvent] = field(default_factory=list)

    async def handle(self, event: ExecutionEvent) -> None:
        self.events.append(event)
