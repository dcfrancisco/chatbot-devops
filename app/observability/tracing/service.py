from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.observability.tracing.correlation import CorrelationContext, get_correlation_context
from app.observability.tracing.exporters import BaseTraceExporter
from app.observability.tracing.replay import InMemoryTraceReplayStore
from app.observability.telemetry.service import TelemetryService
from app.observability.tracing.context import (
    get_span_id,
    get_trace_id,
    reset_span_id,
    reset_trace_context,
    set_span_id,
    set_trace_context,
)
from app.observability.tracing.models import ExecutionTrace, ExecutionTraceSpan, SpanKind


class TracingService:
    def __init__(
        self,
        telemetry_service: TelemetryService,
        replay_store: InMemoryTraceReplayStore | None = None,
        exporters: list[BaseTraceExporter] | None = None,
    ) -> None:
        self._telemetry_service = telemetry_service
        self._replay_store = replay_store or InMemoryTraceReplayStore()
        self._exporters = list(exporters or [])

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
        ).bind_root_span(str(uuid4()))
        await self._telemetry_service.trace_started(trace)
        await self._replay_store.start_trace(trace)
        for exporter in self._exporters:
            await exporter.export_trace_started(trace)
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
        root_started_at = trace.started_at
        tokens = set_trace_context(
            trace_id=trace.trace_id,
            correlation_id=trace.correlation_id,
            span_id=trace.root_span_id,
        )
        status = "ok"
        failure: Exception | None = None
        try:
            yield trace
        except Exception as exc:
            status = "error"
            failure = exc
            raise
        finally:
            completed_trace = trace.complete()
            if trace.root_span_id is not None:
                root_attributes = dict(trace.attributes)
                if failure is not None:
                    root_attributes["exception_type"] = failure.__class__.__name__
                await self._record_span(
                    ExecutionTraceSpan.create(
                        trace_id=completed_trace.trace_id,
                        span_id=trace.root_span_id,
                        name=completed_trace.root_name,
                        status=status,
                        started_at=root_started_at,
                        ended_at=completed_trace.ended_at or datetime.now(timezone.utc),
                        correlation_id=completed_trace.correlation_id,
                        parent_span_id=None,
                        kind=SpanKind.TRACE_ROOT,
                        component="observability",
                        attributes=root_attributes,
                    )
                )
            await self._replay_store.complete_trace(completed_trace)
            for exporter in self._exporters:
                await exporter.export_trace_completed(completed_trace)
            reset_trace_context(tokens)

    @asynccontextmanager
    async def span(
        self,
        name: str,
        *,
        kind: SpanKind = SpanKind.INTERNAL,
        component: str = "runtime",
        **attributes: Any,
    ):
        trace_id = get_trace_id() or str(uuid4())
        correlation_id = get_correlation_context().correlation_id
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
            span = ExecutionTraceSpan.create(
                trace_id=trace_id,
                span_id=span_id,
                name=name,
                status=status,
                started_at=started_at,
                ended_at=ended_at,
                correlation_id=correlation_id,
                parent_span_id=parent_span_id,
                kind=kind,
                component=component,
                attributes=payload,
            )
            await self._record_span(span)

    def current_trace_id(self) -> str | None:
        return get_trace_id()

    def current_correlation_id(self) -> str | None:
        return get_correlation_context().correlation_id

    def current_correlation_context(self) -> CorrelationContext:
        return get_correlation_context()

    def current_propagation_headers(self) -> dict[str, str]:
        return self.current_correlation_context().as_headers()

    async def get_trace_snapshot(self, trace_id: str):
        return await self._replay_store.get_snapshot(trace_id)

    async def _record_span(self, span: ExecutionTraceSpan) -> None:
        await self._telemetry_service.record_span(span)
        await self._replay_store.record_span(span)
        for exporter in self._exporters:
            await exporter.export_span(span)

    async def aclose(self) -> None:
        await self._replay_store.aclose()
        for exporter in self._exporters:
            await exporter.aclose()
        await self._telemetry_service.aclose()