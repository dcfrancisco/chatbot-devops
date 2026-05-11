from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class WorkflowRetryPolicy:
    max_attempts: int = 1
    backoff_seconds: float = 0.0

    def normalized_attempts(self) -> int:
        return max(1, self.max_attempts)


@dataclass(slots=True, frozen=True)
class WorkflowStepDefinition:
    name: str
    handler: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    retry_policy: WorkflowRetryPolicy = field(default_factory=WorkflowRetryPolicy)
    transitions: dict[str, str | None] = field(default_factory=dict)
    terminal: bool = False


@dataclass(slots=True)
class WorkflowDefinition:
    name: str
    description: str
    steps: tuple[WorkflowStepDefinition, ...]
    entry_step: str
    version: str = "1.0.0"
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Workflow definition requires a non-empty name")
        if not self.steps:
            raise ValueError(f"Workflow '{self.name}' must define at least one step")
        step_names = [step.name for step in self.steps]
        if len(step_names) != len(set(step_names)):
            raise ValueError(f"Workflow '{self.name}' defines duplicate step names")
        if self.entry_step not in step_names:
            raise ValueError(f"Workflow '{self.name}' entry step '{self.entry_step}' is not defined")

    @property
    def capabilities(self) -> tuple[str, ...]:
        return self.tags

    def get_step(self, name: str) -> WorkflowStepDefinition:
        for step in self.steps:
            if step.name == name:
                return step
        raise KeyError(f"Unknown workflow step '{name}' for workflow '{self.name}'")

    def next_step(self, current_step: str, outcome_status: str) -> str | None:
        step = self.get_step(current_step)
        if outcome_status in step.transitions:
            return step.transitions[outcome_status]
        if step.terminal:
            return None

        ordered_names = [candidate.name for candidate in self.steps]
        index = ordered_names.index(current_step)
        if index + 1 >= len(ordered_names):
            return None
        return ordered_names[index + 1]

    def metadata_payload(self) -> dict[str, object]:
        return {
            "version": self.version,
            "tags": list(self.tags),
            **self.metadata,
        }