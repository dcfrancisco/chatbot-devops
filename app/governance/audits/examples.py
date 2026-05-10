from __future__ import annotations

from app.core.logging import get_logger
from app.governance.audits.base import BaseAuditSink
from app.governance.audits.models import AuditRecord


class StructuredLogAuditSink(BaseAuditSink):
    name = "structured-log-audit"
    description = "Writes governance audit events into structured application logs."

    def __init__(self) -> None:
        self._logger = get_logger(__name__)

    async def write(self, record: AuditRecord) -> None:
        self._logger.info(
            "governance_audit_recorded",
            extra={
                "record_id": record.record_id,
                "trace_id": record.trace_id,
                "event_type": record.event_type,
                "outcome": record.outcome,
                "reason": record.reason,
                "agent_name": record.agent_name,
                "conversation_id": record.conversation_id,
                "requested_tool": record.requested_tool,
                "metadata": record.metadata,
            },
        )