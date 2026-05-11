from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class TraceState(StrEnum):
    STARTED = "started"
    COMPLETED = "completed"


@dataclass(slots=True, frozen=True)
class ExecutionTrace:
    trace_id: str
    correlation_id: str | None
    root_name: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    duration_ms: int | None = None
    state: TraceState = TraceState.STARTED
    root_span_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    def complete(self, *, ended_at: datetime | None = None) -> ExecutionTrace:
        finished_at = ended_at or datetime.now(timezone.utc)
        return replace(
            self,
            ended_at=finished_at,
            duration_ms=int((finished_at - self.started_at).total_seconds() * 1000),
            state=TraceState.COMPLETED,
        )

    def bind_root_span(self, span_id: str) -> ExecutionTrace:
        return replace(self, root_span_id=span_id)

    @classmethod
    def create(
        cls,
        *,
        trace_id: str | None = None,
        correlation_id: str | None = None,
        root_name: str,
        attributes: dict[str, Any] | None = None,
    ) -> ExecutionTrace:
        return cls(
            trace_id=trace_id or str(uuid4()),
            correlation_id=correlation_id,
            root_name=root_name,
            attributes=attributes or {},
        )