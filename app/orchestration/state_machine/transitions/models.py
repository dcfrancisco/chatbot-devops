from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.orchestration.state_machine.states import RuntimeLifecycleState


@dataclass(slots=True, frozen=True)
class RuntimeStateTransition:
    from_state: RuntimeLifecycleState
    to_state: RuntimeLifecycleState
    step_name: str
    status: str = "completed"
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None