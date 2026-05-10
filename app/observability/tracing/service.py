from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.observability.telemetry.service import TelemetryService
from app.observability.tracing.context import (
    get_correlation_id,
    get_span_id,
    get_trace_id,
    reset_span_id,
    reset_trace_context,
    set_span_id,
    set_trace_context,
)
from app.observability.tracing.models import ExecutionTrace, ExecutionTraceSpan


class TracingService:
    def __init__(self, telemetry_service: TelemetryService) -> None:
        self._telemetry_service = telemetry_service

    async def begin_trace(
        self,
        *,
        root_name: str,
        trace_id: str | None = None,
        correlation_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> ExecutionTrace:
        trace = ExecutionTrace.create(
            trace_id=trace_id or str(uuid4()),
            correlation_id=correlation_id,
            root_name=root_name,
            attributes=attributes,
        )
        await self._telemetry_service.trace_started(trace)
        return trace

    @asynccontextmanager
    async def trace_scope(
        self,
        *,
        root_name: str,
        trace_id: str | None = None,
        correlation_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ):
        trace = await self.begin_trace(
            root_name=root_name,
            trace_id=trace_id,
            correlation_id=correlation_id,
            attributes=attributes,
        )
        tokens = set_trace_context(trace_id=trace.trace_id, correlation_id=trace.correlation_id, span_id=None)
        try:
            yield trace
        finally:
            reset_trace_context(tokens)

    @asynccontextmanager
    async def span(self, name: str, **attributes: Any):
        trace_id = get_trace_id() or str(uuid4())
        correlation_id = get_correlation_id()
        parent_span_id = get_span_id()
        span_id = str(uuid4())
        started_at = datetime.now(timezone.utc)
        token = set_span_id(span_id)
        status = "ok"
        failure: Exception | None = None
        try:
            yield span_id
        except Exception as exc:
            status = "error"
            failure = exc
            raise
        finally:
            reset_span_id(token)
            ended_at = datetime.now(timezone.utc)
            payload = dict(attributes)
            if failure is not None:
                payload["exception_type"] = failure.__class__.__name__
            await self._telemetry_service.record_span(
                ExecutionTraceSpan.create(
                    trace_id=trace_id,
                    span_id=span_id,
                    name=name,
                    status=status,
                    started_at=started_at,
                    ended_at=ended_at,
                    correlation_id=correlation_id,
                    parent_span_id=parent_span_id,
                    attributes=payload,
                )
            )

    def current_trace_id(self) -> str | None:
        return get_trace_id()

    def current_correlation_id(self) -> str | None:
        return get_correlation_id()

    async def aclose(self) -> None:
        await self._telemetry_service.aclose()