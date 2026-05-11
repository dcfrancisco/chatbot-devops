from __future__ import annotations

from app.observability.logging.service import StructuredLoggingService
from app.observability.tracing.execution.models import ExecutionTrace
from app.observability.tracing.exporters.base import BaseTraceExporter
from app.observability.tracing.spans.models import ExecutionTraceSpan


class StructuredTraceLoggerExporter(BaseTraceExporter):
    name = "structured-trace-logger"

    def __init__(self, logging_service: StructuredLoggingService) -> None:
        self._logging_service = logging_service

    async def export_trace_started(self, trace: ExecutionTrace) -> None:
        self._logging_service.info(
            "trace_started",
            trace_id=trace.trace_id,
            correlation_id=trace.correlation_id,
            root_name=trace.root_name,
            attributes=trace.attributes,
        )

    async def export_span(self, span: ExecutionTraceSpan) -> None:
        self._logging_service.info("trace_span_recorded", **span.as_metadata())

    async def export_trace_completed(self, trace: ExecutionTrace) -> None:
        self._logging_service.info(
            "trace_completed",
            trace_id=trace.trace_id,
            correlation_id=trace.correlation_id,
            root_name=trace.root_name,
            duration_ms=trace.duration_ms,
            state=trace.state,
        )


class OpenTelemetryTraceExporterExample(BaseTraceExporter):
    name = "otel-exporter-example"

    async def export_span(self, span: ExecutionTraceSpan) -> None:
        # Placeholder seam for future OpenTelemetry conversion and export.
        _ = {
            "trace_id": span.trace_id,
            "span_id": span.span_id,
            "parent_span_id": span.parent_span_id,
            "name": span.name,
            "kind": span.kind,
            "component": span.component,
            "status": span.status,
            "started_at": span.started_at,
            "ended_at": span.ended_at,
            "attributes": span.attributes,
        }