from __future__ import annotations

from app.orchestration.context import ExecutionContext
from app.orchestration.events.models import EventCorrelation, RuntimeEventName, RuntimeExecutionEvent, TracingExecutionEvent


class EventFactory:
    @staticmethod
    def correlation_from_context(context: ExecutionContext) -> EventCorrelation:
        return EventCorrelation(
            request_id=context.request_id,
            trace_id=context.trace_id,
            correlation_id=context.runtime_metadata.correlation_id,
            conversation_id=context.conversation_id,
            user_id=context.user_id,
        )

    @classmethod
    def runtime_event(
        cls,
        *,
        context: ExecutionContext,
        event_name: RuntimeEventName,
        stage: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> RuntimeExecutionEvent:
        return RuntimeExecutionEvent.create(
            event_name=event_name,
            correlation=cls.correlation_from_context(context),
            stage=stage,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def tracing_event(
        cls,
        *,
        context: ExecutionContext,
        event_name: RuntimeEventName,
        stage: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> TracingExecutionEvent:
        return TracingExecutionEvent.create(
            event_name=event_name,
            correlation=cls.correlation_from_context(context),
            stage=stage,
            metadata=dict(metadata or {}),
        )
