from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any

from app.governance.base import GovernanceDecision
from app.models.api import ToolExecutionResponse
from app.observability.tracing.models import ExecutionTraceSpan


@dataclass(slots=True, frozen=True)
class RuntimeMetadata:
    agent_name: str
    route_name: str = "deterministic"
    environment: str | None = None
    correlation_id: str | None = None
    tags: tuple[str, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)

    def merge_attributes(self, attributes: dict[str, Any]) -> RuntimeMetadata:
        return replace(self, attributes={**self.attributes, **attributes})


@dataclass(slots=True, frozen=True)
class TimingMetadata:
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    duration_ms: int | None = None

    def touch(self, at: datetime | None = None) -> TimingMetadata:
        now = at or datetime.now(timezone.utc)
        return replace(self, last_updated_at=now)

    def complete(self, at: datetime | None = None) -> TimingMetadata:
        ended_at = at or datetime.now(timezone.utc)
        duration_ms = int((ended_at - self.started_at).total_seconds() * 1000)
        return replace(self, last_updated_at=ended_at, completed_at=ended_at, duration_ms=duration_ms)


@dataclass(slots=True, frozen=True)
class GovernanceRecord:
    decision: GovernanceDecision
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True, frozen=True)
class ToolResultRecord:
    response: ToolExecutionResponse
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True, frozen=True)
class ExecutionTraceRecord:
    trace_id: str
    correlation_id: str | None = None
    spans: tuple[ExecutionTraceSpan, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)

    def append_span(self, span: ExecutionTraceSpan) -> ExecutionTraceRecord:
        return replace(self, spans=(*self.spans, span))

    def merge_attributes(self, attributes: dict[str, Any]) -> ExecutionTraceRecord:
        return replace(self, attributes={**self.attributes, **attributes})
