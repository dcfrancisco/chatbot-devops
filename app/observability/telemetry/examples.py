from __future__ import annotations

from app.core.logging import get_logger
from app.observability.telemetry.base import BaseTelemetrySink
from app.observability.tracing.models import ExecutionTrace, ExecutionTraceSpan


class StructuredLogTelemetrySink(BaseTelemetrySink):
    name = "structured-log-telemetry"
    description = "Writes execution traces and spans into structured logs and preserves an OTEL-compatible seam."

    def __init__(self) -> None:
        self._logger = get_logger(__name__)

    async def on_trace_started(self, trace: ExecutionTrace) -> None:
        self._logger.info(
            "trace_started",
            extra={
                "trace_id": trace.trace_id,
                "correlation_id": trace.correlation_id,
                "root_name": trace.root_name,
                "trace_attributes": trace.attributes,
            },
        )

    async def on_span_recorded(self, span: ExecutionTraceSpan) -> None:
        self._logger.info(
            "trace_span_recorded",
            extra={
                "trace_id": span.trace_id,
                "correlation_id": span.correlation_id,
                "span_id": span.span_id,
                "parent_span_id": span.parent_span_id,
                "span_name": span.name,
                "span_status": span.status,
                "duration_ms": span.duration_ms,
                "attributes": span.attributes,
            },
        )


class OpenTelemetryCompatibleSink(BaseTelemetrySink):
    name = "otel-compatible"
    description = "Placeholder sink for future OpenTelemetry exporters."

    async def on_span_recorded(self, span: ExecutionTraceSpan) -> None:
        return None