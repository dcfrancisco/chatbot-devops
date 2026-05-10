from __future__ import annotations

from collections.abc import Iterable

from app.observability.telemetry.base import BaseTelemetrySink
from app.observability.tracing.models import ExecutionTrace, ExecutionTraceSpan


class TelemetryService:
    def __init__(self, sinks: Iterable[BaseTelemetrySink] | None = None) -> None:
        self._sinks = list(sinks or [])

    async def trace_started(self, trace: ExecutionTrace) -> None:
        for sink in self._sinks:
            await sink.on_trace_started(trace)

    async def record_span(self, span: ExecutionTraceSpan) -> None:
        for sink in self._sinks:
            await sink.on_span_recorded(span)

    async def aclose(self) -> None:
        for sink in reversed(self._sinks):
            await sink.aclose()