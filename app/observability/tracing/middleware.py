from __future__ import annotations

from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

class TraceContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get("x-request-id") or str(uuid4())
        trace_id = request.headers.get("x-trace-id") or str(uuid4())
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
            response.headers["x-request-id"] = correlation_id
            response.headers["x-trace-id"] = trace_id
            return response