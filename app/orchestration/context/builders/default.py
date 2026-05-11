from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from app.core.config import Settings
from app.observability.service import ObservabilityService
from app.orchestration.context.builders.base import ExecutionContextBuilder
from app.orchestration.context.execution_context import ExecutionContext
from app.orchestration.context.execution_metadata import ExecutionTraceRecord, RuntimeMetadata
from app.orchestration.context.execution_state import ExecutionStage


class DefaultExecutionContextBuilder(ExecutionContextBuilder):
    def __init__(
        self,
        *,
        settings: Settings,
        observability_service: ObservabilityService,
        request_message: str,
        conversation_id: str | None,
        user_id: str | None,
        request_id: str | None = None,
        agent_name: str | None = None,
        route_name: str = "deterministic",
    ) -> None:
        trace_id = observability_service.current_trace_id() or str(uuid4())
        correlation_id = observability_service.current_correlation_id()
        runtime_metadata = RuntimeMetadata(
            agent_name=agent_name or "conversation",
            route_name=route_name,
            environment=settings.environment,
            correlation_id=correlation_id,
            attributes={"request_message_length": len(request_message), "streaming_supported": True},
        )
        self._context = ExecutionContext(
            request_id=request_id or trace_id,
            conversation_id=conversation_id,
            user_id=user_id,
            trace_id=trace_id,
            runtime_metadata=runtime_metadata,
            request_message=request_message,
            execution_trace=ExecutionTraceRecord(trace_id=trace_id, correlation_id=correlation_id),
        )

    def build(self) -> ExecutionContext:
        return self._context

    def transition(self, stage: ExecutionStage, *, step_name: str, metadata: dict[str, object] | None = None) -> DefaultExecutionContextBuilder:
        self._context = self._context.transition(stage, step_name=step_name, metadata=dict(metadata or {}))
        return self

    def with_runtime_attribute(self, key: str, value: object) -> DefaultExecutionContextBuilder:
        self._context = self._context.with_runtime_attributes({key: value})
        return self

    def with_user_id(self, user_id: str | None) -> DefaultExecutionContextBuilder:
        self._context = replace(self._context, user_id=user_id)
        return self
