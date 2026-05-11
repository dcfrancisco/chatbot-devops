from __future__ import annotations

from dataclasses import dataclass, field

from app.observability.tracing.execution.models import ExecutionTrace
from app.observability.tracing.spans.models import ExecutionTraceSpan


@dataclass(slots=True, frozen=True)
class ReplayNode:
    span: ExecutionTraceSpan
    children: tuple[ReplayNode, ...] = ()


@dataclass(slots=True, frozen=True)
class TraceReplaySnapshot:
    trace: ExecutionTrace
    spans: tuple[ExecutionTraceSpan, ...]
    roots: tuple[ReplayNode, ...] = ()
    span_count: int = 0
    hierarchy_depth: int = 0
    replayable: bool = True
    metadata: dict[str, object] = field(default_factory=dict)