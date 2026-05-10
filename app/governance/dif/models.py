from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


DIFDecisionStatus = Literal["pass", "review", "block"]


@dataclass(slots=True, frozen=True)
class DIFDecision:
    status: DIFDecisionStatus
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)