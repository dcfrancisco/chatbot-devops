from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class CounterMetric:
    name: str
    value: int = 1
    attributes: dict[str, Any] = field(default_factory=dict)