from __future__ import annotations

from collections.abc import Iterable

from app.governance.audits.base import BaseAuditSink
from app.governance.audits.models import AuditRecord


class AuditService:
    def __init__(self, sinks: Iterable[BaseAuditSink] | None = None) -> None:
        self._sinks = list(sinks or [])

    async def record(self, record: AuditRecord) -> AuditRecord:
        for sink in self._sinks:
            await sink.write(record)
        return record

    async def aclose(self) -> None:
        for sink in reversed(self._sinks):
            await sink.aclose()