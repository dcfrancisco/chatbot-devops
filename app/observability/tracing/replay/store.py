from __future__ import annotations

import asyncio

from app.observability.tracing.execution.models import ExecutionTrace
from app.observability.tracing.replay.models import ReplayNode, TraceReplaySnapshot
from app.observability.tracing.spans.models import ExecutionTraceSpan


class InMemoryTraceReplayStore:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._traces: dict[str, ExecutionTrace] = {}
        self._spans: dict[str, list[ExecutionTraceSpan]] = {}

    async def start_trace(self, trace: ExecutionTrace) -> None:
        async with self._lock:
            self._traces[trace.trace_id] = trace
            self._spans.setdefault(trace.trace_id, [])

    async def complete_trace(self, trace: ExecutionTrace) -> None:
        async with self._lock:
            self._traces[trace.trace_id] = trace

    async def record_span(self, span: ExecutionTraceSpan) -> None:
        async with self._lock:
            self._spans.setdefault(span.trace_id, []).append(span)

    async def get_snapshot(self, trace_id: str) -> TraceReplaySnapshot | None:
        async with self._lock:
            trace = self._traces.get(trace_id)
            spans = tuple(self._spans.get(trace_id, []))
        if trace is None:
            return None
        roots = self._build_roots(spans)
        return TraceReplaySnapshot(
            trace=trace,
            spans=spans,
            roots=roots,
            span_count=len(spans),
            hierarchy_depth=self._depth(roots),
            metadata={
                "trace_state": trace.state,
                "root_span_id": trace.root_span_id,
                "root_name": trace.root_name,
            },
        )

    async def aclose(self) -> None:
        async with self._lock:
            self._traces.clear()
            self._spans.clear()

    def _build_roots(self, spans: tuple[ExecutionTraceSpan, ...]) -> tuple[ReplayNode, ...]:
        spans_by_id = {span.span_id: span for span in spans}
        children_by_parent: dict[str | None, list[ExecutionTraceSpan]] = {}
        for span in spans:
            children_by_parent.setdefault(span.parent_span_id, []).append(span)

        def build_node(span: ExecutionTraceSpan) -> ReplayNode:
            return ReplayNode(
                span=span,
                children=tuple(build_node(child) for child in children_by_parent.get(span.span_id, [])),
            )

        orphan_roots = [span for span in spans if span.parent_span_id not in spans_by_id]
        return tuple(build_node(span) for span in orphan_roots)

    def _depth(self, roots: tuple[ReplayNode, ...]) -> int:
        if not roots:
            return 0

        def node_depth(node: ReplayNode) -> int:
            if not node.children:
                return 1
            return 1 + max(node_depth(child) for child in node.children)

        return max(node_depth(root) for root in roots)