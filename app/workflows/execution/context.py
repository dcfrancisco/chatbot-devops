from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.orchestration.context import ExecutionContext
from app.workflows.definitions import WorkflowDefinition
from app.workflows.state import WorkflowRunState


@dataclass(slots=True)
class WorkflowCancellationToken:
    cancelled: bool = False
    reason: str | None = None

    def cancel(self, reason: str = "cancelled_by_operator") -> None:
        self.cancelled = True
        self.reason = reason


@dataclass(slots=True)
class WorkflowExecutionContext:
    definition: WorkflowDefinition
    run_id: str
    trace_id: str
    input_data: dict[str, Any]
    services: dict[str, Any] = field(default_factory=dict)
    session: AsyncSession | None = None
    execution_context: ExecutionContext | None = None
    cancellation_token: WorkflowCancellationToken = field(default_factory=WorkflowCancellationToken)
    variables: dict[str, Any] = field(default_factory=dict)
    run_state: WorkflowRunState | None = None

    def set_run_state(self, state: WorkflowRunState) -> None:
        self.run_state = state

    def merge_output(self, payload: dict[str, Any]) -> None:
        self.variables.update(payload)

    def snapshot(self) -> dict[str, Any]:
        return {
            "input": dict(self.input_data),
            "variables": dict(self.variables),
        }