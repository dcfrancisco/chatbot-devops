from __future__ import annotations

from app.governance.base import GovernanceContext, GovernanceDecision
from app.governance.interceptors.context import GovernanceInterceptorContext
from app.governance.restrictions import ExecutionRestrictionService, RestrictionViolation


class RestrictionEvaluator:
    def __init__(self, restriction_service: ExecutionRestrictionService) -> None:
        self._restriction_service = restriction_service

    def evaluate(
        self,
        context: GovernanceInterceptorContext,
        decision: GovernanceDecision,
    ) -> list[RestrictionViolation]:
        return self._restriction_service.validate(self.to_governance_context(context), decision.restrictions)

    def to_governance_context(self, context: GovernanceInterceptorContext) -> GovernanceContext:
        return GovernanceContext(
            trace_id=context.trace_id,
            agent_name=context.agent_name,
            conversation_id=context.conversation_id,
            message=context.message,
            requested_tool=context.requested_tool,
            tool_arguments=context.tool_arguments,
            metadata={
                **context.metadata,
                "governance_target": context.target,
                "interception_phase": context.phase,
                "workflow_name": context.workflow_name,
                "role_names": list(context.role_names),
                "user_id": context.user_id,
            },
        )
