from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from app.workflows.state import WorkflowRunState, WorkflowStepStatus


@dataclass(slots=True, frozen=True)
class WorkflowStepOutcome:
    status: WorkflowStepStatus = WorkflowStepStatus.COMPLETED
    output: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    next_step: str | None = None

    @classmethod
    def completed(
        cls,
        *,
        output: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        next_step: str | None = None,
    ) -> WorkflowStepOutcome:
        return cls(
            status=WorkflowStepStatus.COMPLETED,
            output=output or {},
            metadata=metadata or {},
            next_step=next_step,
        )


@dataclass(slots=True, frozen=True)
class WorkflowRunResult:
    state: WorkflowRunState
    output: dict[str, Any] = field(default_factory=dict)


WorkflowStateListener = Callable[[WorkflowRunState], Awaitable[None] | None]