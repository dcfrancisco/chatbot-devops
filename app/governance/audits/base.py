from __future__ import annotations

from abc import ABC, abstractmethod

from app.governance.audits.models import AuditRecord


class BaseAuditSink(ABC):
    name: str
    description: str

    @abstractmethod
    async def write(self, record: AuditRecord) -> None:
        raise NotImplementedError

    async def aclose(self) -> None:
        return None