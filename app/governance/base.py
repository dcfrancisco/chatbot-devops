from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.governance.approvals.models import ApprovalResolution
from app.governance.audits.models import AuditRecord
from app.governance.restrictions.models import RestrictionSet


@dataclass(slots=True)
class GovernanceContext:
    trace_id: str
    agent_name: str
    conversation_id: str | None
    message: str
    requested_tool: str | None = None
    tool_arguments: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GovernanceDecision:
    allowed: bool = True
    requires_approval: bool = False
    reason: str = "allowed"
    violations: tuple[str, ...] = ()
    restrictions: RestrictionSet = field(default_factory=RestrictionSet)
    approval: ApprovalResolution | None = None
    audit_record: AuditRecord | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseGovernanceModule(ABC):
    name: str
    description: str

    @abstractmethod
    async def evaluate(self, context: GovernanceContext) -> GovernanceDecision:
        raise NotImplementedError