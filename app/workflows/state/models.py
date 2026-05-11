from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_APPROVAL = "awaiting_approval"
    CANCELLED = "cancelled"


@dataclass(slots=True, frozen=True)
class WorkflowStepRunState:
    name: str
    handler: str
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    attempts: int = 0
    started_at: datetime | None = None
    ended_at: datetime | None = None
    input_snapshot: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


@dataclass(slots=True, frozen=True)
class WorkflowRunState:
    run_id: str
    workflow_name: str
    workflow_version: str
    trace_id: str
    request_id: str
    correlation_id: str | None = None
    conversation_id: str | None = None
    user_id: str | None = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: str | None = None
    input_data: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    steps: tuple[WorkflowStepRunState, ...] = ()
    cancellation_reason: str | None = None
    failure_reason: str | None = None

    @classmethod
    def create(
        cls,
        *,
        workflow_name: str,
        workflow_version: str,
        trace_id: str,
        request_id: str | None,
        correlation_id: str | None,
        conversation_id: str | None,
        user_id: str | None,
        input_data: dict[str, Any],
        run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowRunState:
        return cls(
            run_id=run_id or str(uuid4()),
            workflow_name=workflow_name,
            workflow_version=workflow_version,
            trace_id=trace_id,
            request_id=request_id or run_id or str(uuid4()),
            correlation_id=correlation_id,
            conversation_id=conversation_id,
            user_id=user_id,
            input_data=dict(input_data),
            metadata=metadata or {},
        )

    def start(self) -> WorkflowRunState:
        return replace(self, status=WorkflowStatus.RUNNING, started_at=self.started_at or _utcnow())

    def start_step(self, *, step_name: str, handler: str, input_snapshot: dict[str, Any], metadata: dict[str, Any] | None = None) -> WorkflowRunState:
        existing = self.step(step_name)
        next_state = WorkflowStepRunState(
            name=step_name,
            handler=handler,
            status=WorkflowStepStatus.RUNNING,
            attempts=(existing.attempts if existing is not None else 0) + 1,
            started_at=existing.started_at or _utcnow() if existing is not None else _utcnow(),
            ended_at=None,
            input_snapshot=input_snapshot,
            output=existing.output if existing is not None else {},
            metadata={**(existing.metadata if existing is not None else {}), **(metadata or {})},
            error_message=None,
        )
        return replace(self, current_step=step_name, steps=self._upsert_step(next_state), status=WorkflowStatus.RUNNING)

    def retry_step(self, *, step_name: str, error_message: str, metadata: dict[str, Any] | None = None) -> WorkflowRunState:
        current = self._require_step(step_name)
        next_state = replace(
            current,
            status=WorkflowStepStatus.RETRYING,
            ended_at=_utcnow(),
            metadata={**current.metadata, **(metadata or {})},
            error_message=error_message,
        )
        return replace(self, steps=self._upsert_step(next_state))

    def complete_step(self, *, step_name: str, output: dict[str, Any], metadata: dict[str, Any] | None = None) -> WorkflowRunState:
        current = self._require_step(step_name)
        next_state = replace(
            current,
            status=WorkflowStepStatus.COMPLETED,
            ended_at=_utcnow(),
            output=dict(output),
            metadata={**current.metadata, **(metadata or {})},
            error_message=None,
        )
        return replace(self, steps=self._upsert_step(next_state), output={**self.output, **output})

    def await_approval(self, *, step_name: str, metadata: dict[str, Any] | None = None) -> WorkflowRunState:
        current = self._require_step(step_name)
        next_state = replace(
            current,
            status=WorkflowStepStatus.AWAITING_APPROVAL,
            ended_at=_utcnow(),
            metadata={**current.metadata, **(metadata or {})},
        )
        return replace(
            self,
            steps=self._upsert_step(next_state),
            status=WorkflowStatus.AWAITING_APPROVAL,
            current_step=step_name,
        )

    def fail_step(self, *, step_name: str, error_message: str, metadata: dict[str, Any] | None = None) -> WorkflowRunState:
        current = self._require_step(step_name)
        next_state = replace(
            current,
            status=WorkflowStepStatus.FAILED,
            ended_at=_utcnow(),
            metadata={**current.metadata, **(metadata or {})},
            error_message=error_message,
        )
        return replace(
            self,
            steps=self._upsert_step(next_state),
            status=WorkflowStatus.FAILED,
            failure_reason=error_message,
            ended_at=_utcnow(),
        )

    def cancel(self, *, step_name: str | None = None, reason: str) -> WorkflowRunState:
        steps = self.steps
        if step_name is not None and self.step(step_name) is not None:
            current = self._require_step(step_name)
            next_state = replace(current, status=WorkflowStepStatus.CANCELLED, ended_at=_utcnow(), error_message=reason)
            steps = self._upsert_step(next_state)
        return replace(
            self,
            steps=steps,
            status=WorkflowStatus.CANCELLED,
            cancellation_reason=reason,
            ended_at=_utcnow(),
        )

    def complete(self, *, output: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> WorkflowRunState:
        merged_output = {**self.output, **(output or {})}
        return replace(
            self,
            status=WorkflowStatus.COMPLETED,
            output=merged_output,
            metadata={**self.metadata, **(metadata or {})},
            current_step=None,
            ended_at=_utcnow(),
        )

    def fail(self, *, reason: str, metadata: dict[str, Any] | None = None) -> WorkflowRunState:
        return replace(
            self,
            status=WorkflowStatus.FAILED,
            metadata={**self.metadata, **(metadata or {})},
            failure_reason=reason,
            ended_at=_utcnow(),
        )

    def step(self, name: str) -> WorkflowStepRunState | None:
        for step in self.steps:
            if step.name == name:
                return step
        return None

    def _require_step(self, name: str) -> WorkflowStepRunState:
        step = self.step(name)
        if step is None:
            raise KeyError(f"Workflow step '{name}' has not been started")
        return step

    def _upsert_step(self, next_step: WorkflowStepRunState) -> tuple[WorkflowStepRunState, ...]:
        updated = []
        replaced = False
        for step in self.steps:
            if step.name == next_step.name:
                updated.append(next_step)
                replaced = True
            else:
                updated.append(step)
        if not replaced:
            updated.append(next_step)
        return tuple(updated)