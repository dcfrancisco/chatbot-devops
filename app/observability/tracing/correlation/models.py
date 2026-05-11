from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(slots=True, frozen=True)
class CorrelationContext:
    trace_id: str | None
    correlation_id: str | None
    span_id: str | None = None

    def as_metadata(self) -> dict[str, str | None]:
        return {
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "span_id": self.span_id,
        }

    def as_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.correlation_id is not None:
            headers["x-request-id"] = self.correlation_id
        if self.trace_id is not None:
            headers["x-trace-id"] = self.trace_id
        if self.span_id is not None:
            headers["x-span-id"] = self.span_id
        return headers

    @classmethod
    def from_headers(cls, headers: Mapping[str, str]) -> CorrelationContext:
        lowered = {key.lower(): value for key, value in headers.items()}
        return cls(
            trace_id=lowered.get("x-trace-id"),
            correlation_id=lowered.get("x-request-id"),
            span_id=lowered.get("x-span-id"),
        )