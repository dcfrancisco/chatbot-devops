from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(slots=True, frozen=True)
class ExecutionTraceSpan:
    trace_id: str
    span_id: str
    name: str
    status: str
    started_at: datetime
    ended_at: datetime
    duration_ms: int
    correlation_id: str | None
    parent_span_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        trace_id: str,
        span_id: str,
        name: str,
        status: str,
        started_at: datetime,
        ended_at: datetime,
        correlation_id: str | None,
        parent_span_id: str | None,
        attributes: dict[str, Any] | None = None,
    ) -> ExecutionTraceSpan:
        return cls(
            trace_id=trace_id,
            span_id=span_id,
            name=name,
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=int((ended_at - started_at).total_seconds() * 1000),
            correlation_id=correlation_id,
            parent_span_id=parent_span_id,
            attributes=attributes or {},
        )


@dataclass(slots=True, frozen=True)
class ExecutionTrace:
    trace_id: str
    correlation_id: str | None
    root_name: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    attributes: dict[str, Any] = field(default_factory=dict)

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