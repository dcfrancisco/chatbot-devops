from __future__ import annotations

from uuid import uuid4

from app.observability.tracing.correlation import CorrelationContext
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class TraceContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming_context = CorrelationContext.from_headers(request.headers)
        correlation_id = incoming_context.correlation_id or str(uuid4())
        trace_id = incoming_context.trace_id or str(uuid4())
        correlation_context = CorrelationContext(trace_id=trace_id, correlation_id=correlation_id)
        observability_service = request.app.state.container.observability_service
        async with observability_service.trace_scope(
            root_name=f"http.{request.method.lower()} {request.url.path}",
            trace_id=trace_id,
            correlation_id=correlation_id,
            attributes={"method": request.method, "path": request.url.path},
        ):
            request.state.trace_id = trace_id
            request.state.correlation_id = correlation_id
            response = await call_next(request)
            for header_name, header_value in correlation_context.as_headers().items():
                response.headers[header_name] = header_value
            return response