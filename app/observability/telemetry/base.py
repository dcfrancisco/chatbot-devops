from __future__ import annotations

from abc import ABC, abstractmethod

from app.observability.tracing.models import ExecutionTrace, ExecutionTraceSpan


class BaseTelemetrySink(ABC):
    name: str
    description: str

    async def on_trace_started(self, trace: ExecutionTrace) -> None:
        return None

    @abstractmethod
    async def on_span_recorded(self, span: ExecutionTraceSpan) -> None:
        raise NotImplementedError

    async def aclose(self) -> None:
        return None