from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.orchestration.events.models import EventCorrelation, ExecutionEvent, RuntimeEventName


class WorkflowEventName(StrEnum):
    WORKFLOW_STARTED = RuntimeEventName.WORKFLOW_STARTED
    WORKFLOW_STEP_STARTED = RuntimeEventName.WORKFLOW_STEP_STARTED
    WORKFLOW_STEP_RETRIED = RuntimeEventName.WORKFLOW_STEP_RETRIED
    WORKFLOW_STEP_COMPLETED = RuntimeEventName.WORKFLOW_STEP_COMPLETED
    WORKFLOW_AWAITING_APPROVAL = RuntimeEventName.WORKFLOW_AWAITING_APPROVAL
    WORKFLOW_CANCELLED = RuntimeEventName.WORKFLOW_CANCELLED
    WORKFLOW_COMPLETED = RuntimeEventName.WORKFLOW_COMPLETED
    WORKFLOW_FAILED = RuntimeEventName.WORKFLOW_FAILED


@dataclass(slots=True, frozen=True)
class WorkflowEvent:
    envelope: ExecutionEvent

    @classmethod
    def create(
        cls,
        *,
        event_name: RuntimeEventName,
        correlation: EventCorrelation,
        stage: str | None = None,
        event_type: str = "workflow",
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowEvent:
        return cls(
            envelope=ExecutionEvent.create(
                event_name=event_name,
                event_type=event_type,
                correlation=correlation,
                stage=stage,
                publisher="workflow",
                metadata=metadata,
            )
        )