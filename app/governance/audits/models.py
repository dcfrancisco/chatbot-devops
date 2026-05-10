from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(slots=True, frozen=True)
class AuditRecord:
    record_id: str
    trace_id: str
    event_type: str
    outcome: str
    reason: str
    agent_name: str
    conversation_id: str | None
    requested_tool: str | None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        trace_id: str,
        event_type: str,
        outcome: str,
        reason: str,
        agent_name: str,
        conversation_id: str | None,
        requested_tool: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditRecord:
        return cls(
            record_id=str(uuid4()),
            trace_id=trace_id,
            event_type=event_type,
            outcome=outcome,
            reason=reason,
            agent_name=agent_name,
            conversation_id=conversation_id,
            requested_tool=requested_tool,
            metadata=metadata or {},
        )