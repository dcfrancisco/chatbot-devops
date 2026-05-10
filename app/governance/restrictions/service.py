from __future__ import annotations

from typing import TYPE_CHECKING

from app.governance.restrictions.models import RestrictionSet, RestrictionViolation

if TYPE_CHECKING:
    from app.governance.base import GovernanceContext


class ExecutionRestrictionService:
    def validate(self, context: GovernanceContext, restrictions: RestrictionSet) -> list[RestrictionViolation]:
        violations: list[RestrictionViolation] = []

        if restrictions.allowed_agents and context.agent_name not in restrictions.allowed_agents:
            violations.append(
                RestrictionViolation(
                    code="agent_not_allowed",
                    message=f"Agent '{context.agent_name}' is not allowed by governance policy.",
                    metadata={"agent_name": context.agent_name},
                )
            )

        if restrictions.max_message_chars is not None and len(context.message) > restrictions.max_message_chars:
            violations.append(
                RestrictionViolation(
                    code="message_too_long",
                    message=f"Message exceeded governance limit of {restrictions.max_message_chars} characters.",
                    metadata={"message_length": len(context.message)},
                )
            )

        if context.requested_tool is None:
            return violations

        if not restrictions.tool_execution_enabled:
            violations.append(
                RestrictionViolation(
                    code="tool_execution_disabled",
                    message="Tool execution is disabled by governance policy.",
                    metadata={"tool_name": context.requested_tool},
                )
            )
            return violations

        if restrictions.allowed_tools and context.requested_tool not in restrictions.allowed_tools:
            violations.append(
                RestrictionViolation(
                    code="tool_not_allowlisted",
                    message=f"Tool '{context.requested_tool}' is not in the governance allowlist.",
                    metadata={"tool_name": context.requested_tool},
                )
            )

        if context.requested_tool in restrictions.blocked_tools:
            violations.append(
                RestrictionViolation(
                    code="tool_blocked",
                    message=f"Tool '{context.requested_tool}' is blocked by governance policy.",
                    metadata={"tool_name": context.requested_tool},
                )
            )

        return violations