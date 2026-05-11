from __future__ import annotations

from abc import ABC, abstractmethod

from app.observability.tracing.execution.models import ExecutionTrace
from app.observability.tracing.spans.models import ExecutionTraceSpan


class BaseTraceExporter(ABC):
    name: str

    async def export_trace_started(self, trace: ExecutionTrace) -> None:
        return None

    @abstractmethod
    async def export_span(self, span: ExecutionTraceSpan) -> None:
        raise NotImplementedError

    async def export_trace_completed(self, trace: ExecutionTrace) -> None:
        return None

    async def aclose(self) -> None:
        return None