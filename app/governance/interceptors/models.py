from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.governance.base import GovernanceDecision
from app.governance.interceptors.context import GovernanceTarget, InterceptionPhase


@dataclass(slots=True, frozen=True)
class InterceptorDecision:
    allowed: bool
    phase: InterceptionPhase
    target: GovernanceTarget
    governance_decision: GovernanceDecision
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class InterceptorOutcome:
    target: GovernanceTarget
    phase: InterceptionPhase
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)
