from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class StateMachineTraceSnapshot:
    current_state: str
    transition_count: int
    last_transition: dict[str, Any] | None = None
    recoverable: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)