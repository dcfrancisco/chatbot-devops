from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class GovernanceTarget(StrEnum):
    TOOL_EXECUTION = "tool_execution"
    WORKFLOW_EXECUTION = "workflow_execution"
    PROMPT_GENERATION = "prompt_generation"
    MEMORY_ACCESS = "memory_access"
    RETRIEVAL_ACCESS = "retrieval_access"


class InterceptionPhase(StrEnum):
    PRE_EXECUTION = "pre_execution"
    POST_EXECUTION = "post_execution"


@dataclass(slots=True, frozen=True)
class GovernanceInterceptorContext:
    trace_id: str
    agent_name: str
    conversation_id: str | None
    user_id: str | None
    message: str
    target: GovernanceTarget
    phase: InterceptionPhase
    requested_tool: str | None = None
    tool_arguments: dict[str, Any] = field(default_factory=dict)
    workflow_name: str | None = None
    role_names: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_phase(self, phase: InterceptionPhase, *, metadata: dict[str, Any] | None = None) -> GovernanceInterceptorContext:
        return GovernanceInterceptorContext(
            trace_id=self.trace_id,
            agent_name=self.agent_name,
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            message=self.message,
            target=self.target,
            phase=phase,
            requested_tool=self.requested_tool,
            tool_arguments=dict(self.tool_arguments),
            workflow_name=self.workflow_name,
            role_names=self.role_names,
            metadata={**self.metadata, **(metadata or {})},
        )
