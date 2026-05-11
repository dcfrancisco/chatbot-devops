from __future__ import annotations

from abc import ABC, abstractmethod

from app.orchestration.events.models import ExecutionEvent


class EventSubscriber(ABC):
    name: str

    def accepts(self, event: ExecutionEvent) -> bool:
        return True

    @abstractmethod
    async def handle(self, event: ExecutionEvent) -> None:
        raise NotImplementedError

    async def aclose(self) -> None:
        return None
