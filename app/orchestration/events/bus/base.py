from __future__ import annotations

from abc import ABC, abstractmethod

from app.orchestration.events.models import ExecutionEvent
from app.orchestration.events.subscribers import EventSubscriber


class EventBus(ABC):
    @abstractmethod
    async def publish(self, event: ExecutionEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    def subscribe(self, subscriber: EventSubscriber) -> None:
        raise NotImplementedError

    @abstractmethod
    async def aclose(self) -> None:
        raise NotImplementedError
