from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession


RequestT = TypeVar("RequestT")
ResponseT = TypeVar("ResponseT")


class BaseAgent(ABC, Generic[RequestT, ResponseT]):
    name: str
    description: str
    capabilities: tuple[str, ...] = ()

    @abstractmethod
    async def run(self, session: AsyncSession, request: RequestT) -> ResponseT:
        raise NotImplementedError

    async def stream(self, session: AsyncSession, request: RequestT) -> AsyncIterator[str]:
        del session, request
        raise NotImplementedError(f"Agent '{self.name}' does not support streaming")

    def metadata(self) -> dict[str, object]:
        return {"capabilities": list(self.capabilities)}