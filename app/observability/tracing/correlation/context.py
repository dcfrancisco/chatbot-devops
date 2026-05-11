from __future__ import annotations

from contextvars import ContextVar, Token

from app.observability.tracing.correlation.models import CorrelationContext


_trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
_correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)
_span_id_var: ContextVar[str | None] = ContextVar("span_id", default=None)


def get_trace_id() -> str | None:
    return _trace_id_var.get()


def get_correlation_id() -> str | None:
    return _correlation_id_var.get()


def get_span_id() -> str | None:
    return _span_id_var.get()


def get_correlation_context() -> CorrelationContext:
    return CorrelationContext(
        trace_id=get_trace_id(),
        correlation_id=get_correlation_id(),
        span_id=get_span_id(),
    )


def set_trace_context(
    *,
    trace_id: str | None,
    correlation_id: str | None,
    span_id: str | None = None,
) -> tuple[Token[str | None], Token[str | None], Token[str | None]]:
    return (
        _trace_id_var.set(trace_id),
        _correlation_id_var.set(correlation_id),
        _span_id_var.set(span_id),
    )


def set_span_id(span_id: str | None) -> Token[str | None]:
    return _span_id_var.set(span_id)


def reset_correlation_context(tokens: tuple[Token[str | None], Token[str | None], Token[str | None]]) -> None:
    _trace_id_var.reset(tokens[0])
    _correlation_id_var.reset(tokens[1])
    _span_id_var.reset(tokens[2])


def reset_span_id(token: Token[str | None]) -> None:
    _span_id_var.reset(token)


def clear_trace_context() -> tuple[Token[str | None], Token[str | None], Token[str | None]]:
    return set_trace_context(trace_id=None, correlation_id=None, span_id=None)