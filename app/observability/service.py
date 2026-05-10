from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from app.observability.logging.service import StructuredLoggingService
from app.observability.metrics.models import CounterMetric
from app.observability.metrics.service import MetricsService
from app.observability.telemetry.service import TelemetryService
from app.observability.tracing.service import TracingService


class ObservabilityService:
    def __init__(
        self,
        tracing_service: TracingService,
        telemetry_service: TelemetryService,
        metrics_service: MetricsService,
        logging_service: StructuredLoggingService,
    ) -> None:
        self._tracing_service = tracing_service
        self._telemetry_service = telemetry_service
        self._metrics_service = metrics_service
        self._logging_service = logging_service

    @asynccontextmanager
    async def trace_scope(self, *, root_name: str, trace_id: str | None = None, correlation_id: str | None = None, attributes: dict[str, Any] | None = None):
        async with self._tracing_service.trace_scope(
            root_name=root_name,
            trace_id=trace_id,
            correlation_id=correlation_id,
            attributes=attributes,
        ) as trace:
            yield trace

    @asynccontextmanager
    async def span(self, name: str, **attributes: Any):
        async with self._tracing_service.span(name, **attributes):
            yield

    def current_trace_id(self) -> str | None:
        return self._tracing_service.current_trace_id()

    def current_correlation_id(self) -> str | None:
        return self._tracing_service.current_correlation_id()

    def increment(self, name: str, value: int = 1, **attributes: Any) -> None:
        self._metrics_service.increment(CounterMetric(name=name, value=value, attributes=attributes))

    def log_info(self, event: str, **metadata: Any) -> None:
        self._logging_service.info(event, **metadata)

    def metrics_snapshot(self) -> dict[str, int]:
        return self._metrics_service.snapshot()

    async def aclose(self) -> None:
        await self._tracing_service.aclose()