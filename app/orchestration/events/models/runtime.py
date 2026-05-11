from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.orchestration.events.models.base import EventCorrelation, ExecutionEvent, RuntimeEventName


@dataclass(slots=True, frozen=True)
class RuntimeExecutionEvent:
    envelope: ExecutionEvent

    @classmethod
    def create(
        cls,
        *,
        event_name: RuntimeEventName,
        correlation: EventCorrelation,
        stage: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RuntimeExecutionEvent:
        return cls(
            envelope=ExecutionEvent.create(
                event_name=event_name,
                event_type="runtime",
                correlation=correlation,
                stage=stage,
                metadata=metadata,
            )
        )


@dataclass(slots=True, frozen=True)
class TracingExecutionEvent:
    envelope: ExecutionEvent

    @classmethod
    def create(
        cls,
        *,
        event_name: RuntimeEventName,
        correlation: EventCorrelation,
        stage: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TracingExecutionEvent:
        return cls(
            envelope=ExecutionEvent.create(
                event_name=event_name,
                event_type="trace",
                correlation=correlation,
                stage=stage,
                publisher="tracing",
                metadata=metadata,
            )
        )
