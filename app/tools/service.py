from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.logging import get_logger
from app.models.api import ToolExecutionError, ToolExecutionRequest, ToolExecutionResponse, ToolExecutionTrace
from app.observability.service import ObservabilityService
from app.tools.base import ToolExecutionContext
from app.tools.registry import ToolNotFoundError, ToolRegistry


RETRYABLE_EXCEPTIONS = (httpx.HTTPError, TimeoutError, asyncio.TimeoutError)


class ToolExecutionService:
    def __init__(self, tool_registry: ToolRegistry, observability_service: ObservabilityService) -> None:
        self._tool_registry = tool_registry
        self._observability_service = observability_service
        self._logger = get_logger(__name__)

    def list_tools(self):
        return [tool.describe() for tool in self._tool_registry.list()]

    def get_tool(self, name: str):
        return self._tool_registry.get(name).describe()

    async def execute(self, session: AsyncSession, request: ToolExecutionRequest) -> ToolExecutionResponse:
        started_at = datetime.now(timezone.utc)
        trace_id = self._observability_service.current_trace_id() or str(uuid4())
        attempts = 0

        try:
            tool = self._tool_registry.get(request.name)
        except ToolNotFoundError as exc:
            completed_at = datetime.now(timezone.utc)
            return self._error_response(
                name=request.name,
                status="error",
                code="tool_not_found",
                message=str(exc),
                retryable=False,
                trace_id=trace_id,
                started_at=started_at,
                completed_at=completed_at,
                attempts=attempts,
                timeout_seconds=0.0,
            )

        try:
            validated_arguments = tool.validate_arguments(request.arguments)
        except ValidationError as exc:
            completed_at = datetime.now(timezone.utc)
            return self._error_response(
                name=request.name,
                status="error",
                code="invalid_arguments",
                message=exc.json(),
                retryable=False,
                trace_id=trace_id,
                started_at=started_at,
                completed_at=completed_at,
                attempts=attempts,
                timeout_seconds=tool.timeout_seconds,
            )

        self._logger.info(
            "tool_execution_started",
            extra={
                "trace_id": trace_id,
                "tool_name": tool.name,
                "timeout_seconds": tool.timeout_seconds,
                "retry_attempts": tool.retry_attempts,
                **tool.trace_payload(validated_arguments),
            },
        )

        try:
            result: dict[str, Any] | None = None
            async with self._observability_service.span("tool.execution.attempts", tool_name=tool.name):
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(max(1, tool.retry_attempts)),
                    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
                    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
                    reraise=True,
                ):
                    with attempt:
                        attempts += 1
                        async with asyncio.timeout(tool.timeout_seconds):
                            result = await tool.execute(
                                ToolExecutionContext(session=session, trace_id=trace_id),
                                validated_arguments,
                            )
            completed_at = datetime.now(timezone.utc)
            self._logger.info(
                "tool_execution_completed",
                extra={
                    "trace_id": trace_id,
                    "tool_name": tool.name,
                    "attempts": attempts,
                    "duration_ms": self._duration_ms(started_at, completed_at),
                },
            )
            return ToolExecutionResponse(
                name=tool.name,
                status="success",
                data=result or {},
                trace=self._trace(trace_id, started_at, completed_at, attempts, tool.timeout_seconds),
            )
        except (TimeoutError, asyncio.TimeoutError) as exc:
            completed_at = datetime.now(timezone.utc)
            self._logger.warning(
                "tool_execution_timed_out",
                extra={
                    "trace_id": trace_id,
                    "tool_name": tool.name,
                    "attempts": attempts,
                    "duration_ms": self._duration_ms(started_at, completed_at),
                },
            )
            return self._error_response(
                name=tool.name,
                status="timeout",
                code="execution_timeout",
                message=str(exc) or f"Tool '{tool.name}' exceeded timeout",
                retryable=True,
                trace_id=trace_id,
                started_at=started_at,
                completed_at=completed_at,
                attempts=attempts,
                timeout_seconds=tool.timeout_seconds,
            )
        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            self._logger.exception(
                "tool_execution_failed",
                extra={
                    "trace_id": trace_id,
                    "tool_name": tool.name,
                    "attempts": attempts,
                    "duration_ms": self._duration_ms(started_at, completed_at),
                },
            )
            return self._error_response(
                name=tool.name,
                status="error",
                code="execution_failed",
                message=str(exc),
                retryable=isinstance(exc, RETRYABLE_EXCEPTIONS),
                trace_id=trace_id,
                started_at=started_at,
                completed_at=completed_at,
                attempts=attempts,
                timeout_seconds=tool.timeout_seconds,
            )

    def _error_response(
        self,
        *,
        name: str,
        status: str,
        code: str,
        message: str,
        retryable: bool,
        trace_id: str,
        started_at: datetime,
        completed_at: datetime,
        attempts: int,
        timeout_seconds: float,
    ) -> ToolExecutionResponse:
        return ToolExecutionResponse(
            name=name,
            status=status,
            error=ToolExecutionError(code=code, message=message, retryable=retryable),
            trace=self._trace(trace_id, started_at, completed_at, attempts, timeout_seconds),
        )

    def _trace(
        self,
        trace_id: str,
        started_at: datetime,
        completed_at: datetime,
        attempts: int,
        timeout_seconds: float,
    ) -> ToolExecutionTrace:
        return ToolExecutionTrace(
            trace_id=trace_id,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=self._duration_ms(started_at, completed_at),
            attempts=attempts,
            timeout_seconds=timeout_seconds,
        )

    def _duration_ms(self, started_at: datetime, completed_at: datetime) -> int:
        return int((completed_at - started_at).total_seconds() * 1000)