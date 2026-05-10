from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


ApprovalStatus = Literal["approved", "denied", "pending", "not_required"]


@dataclass(slots=True, frozen=True)
class ApprovalRequest:
    trace_id: str
    agent_name: str
    conversation_id: str | None
    requested_tool: str | None
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ApprovalResolution:
    status: ApprovalStatus
    reason: str
    approver: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)