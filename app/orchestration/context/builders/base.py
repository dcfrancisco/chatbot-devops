from __future__ import annotations

from typing import Protocol

from app.orchestration.context.execution_context import ExecutionContext
from app.orchestration.context.execution_state import ExecutionStage


class ExecutionContextBuilder(Protocol):
    def build(self) -> ExecutionContext:
        ...

    def transition(self, stage: ExecutionStage, *, step_name: str, metadata: dict[str, object] | None = None) -> ExecutionContextBuilder:
        ...
