from __future__ import annotations

import asyncio

from app.orchestration.events.bus.base import EventBus
from app.orchestration.events.models import ExecutionEvent
from app.orchestration.events.subscribers import EventSubscriber


class InMemoryEventBus(EventBus):
    """Async event bus with a local in-memory transport.

    This is the default runtime transport and preserves a clear seam for future
    distributed implementations backed by queues or streams.
    """

    def __init__(self, subscribers: list[EventSubscriber] | None = None) -> None:
        self._subscribers = list(subscribers or [])

    async def publish(self, event: ExecutionEvent) -> None:
        handlers = [subscriber.handle(event) for subscriber in self._subscribers if subscriber.accepts(event)]
        if handlers:
            await asyncio.gather(*handlers)

    def subscribe(self, subscriber: EventSubscriber) -> None:
        self._subscribers.append(subscriber)

    async def aclose(self) -> None:
        for subscriber in reversed(self._subscribers):
            await subscriber.aclose()
