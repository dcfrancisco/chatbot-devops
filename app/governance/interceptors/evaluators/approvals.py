from __future__ import annotations

from app.governance.approvals import ApprovalRequest, ApprovalResolution, ApprovalService
from app.governance.base import GovernanceDecision
from app.governance.interceptors.context import GovernanceInterceptorContext


class ApprovalEvaluator:
    def __init__(self, approval_service: ApprovalService) -> None:
        self._approval_service = approval_service

    async def evaluate(
        self,
        context: GovernanceInterceptorContext,
        decision: GovernanceDecision,
        *,
        violation_codes: list[str],
        dif_status: str,
    ) -> ApprovalResolution:
        approval_required = decision.requires_approval
        if context.requested_tool and context.requested_tool in decision.restrictions.approval_required_tools:
            approval_required = True
        if not approval_required:
            return ApprovalResolution(status="not_required", reason="not_required")
        return await self._approval_service.resolve(
            ApprovalRequest(
                trace_id=context.trace_id,
                agent_name=context.agent_name,
                conversation_id=context.conversation_id,
                requested_tool=context.requested_tool,
                reason=decision.reason,
                metadata={
                    "violations": violation_codes,
                    "dif_status": dif_status,
                    "target": context.target,
                    "phase": context.phase,
                    "workflow_name": context.workflow_name,
                    "user_id": context.user_id,
                    "role_names": list(context.role_names),
                },
            )
        )
