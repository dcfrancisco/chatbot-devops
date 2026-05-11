from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class SpanKind(StrEnum):
    TRACE_ROOT = "trace_root"
    PIPELINE_STAGE = "pipeline_stage"
    AGENT_EXECUTION = "agent_execution"
    TOOL_EXECUTION = "tool_execution"
    MEMORY_RETRIEVAL = "memory_retrieval"
    KB_RETRIEVAL = "kb_retrieval"
    PROMPT_ASSEMBLY = "prompt_assembly"
    LLM_EXECUTION = "llm_execution"
    GOVERNANCE = "governance"
    WORKFLOW = "workflow"
    INTERNAL = "internal"


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
    kind: SpanKind = SpanKind.INTERNAL
    component: str = "runtime"
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def is_root(self) -> bool:
        return self.parent_span_id is None

    def as_metadata(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "status": self.status,
            "kind": self.kind,
            "component": self.component,
            "duration_ms": self.duration_ms,
            "correlation_id": self.correlation_id,
            "attributes": self.attributes,
        }

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
        kind: SpanKind = SpanKind.INTERNAL,
        component: str = "runtime",
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
            kind=kind,
            component=component,
            attributes=attributes or {},
        )