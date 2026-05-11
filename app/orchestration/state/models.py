from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.orchestration.context.execution_context import ExecutionContext
from app.orchestration.context.execution_state import ExecutionStage, ExecutionState, ExecutionStep, ToolPlan


@dataclass(slots=True)
class OrchestrationRuntimeState:
    trace_id: str
    agent_name: str
    conversation_id: str | None
    route_name: str = "deterministic"
    selected_tool: str | None = None
    steps: list[ExecutionStep] = field(default_factory=list)

    def record(self, name: str, **metadata: Any) -> None:
        self.steps.append(ExecutionStep(name=name, stage=ExecutionStage.CREATED, metadata=metadata))


TurnContext = ExecutionContext

__all__ = ["ExecutionStage", "ExecutionState", "ExecutionStep", "OrchestrationRuntimeState", "ToolPlan", "TurnContext"]