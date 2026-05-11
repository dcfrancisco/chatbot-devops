from __future__ import annotations

from app.governance.audits import AuditRecord, AuditService
from app.governance.base import GovernanceDecision
from app.governance.dif import DIFService
from app.governance.interceptors.context import GovernanceInterceptorContext, GovernanceTarget, InterceptionPhase
from app.governance.interceptors.evaluators import ApprovalEvaluator, PolicyEvaluator, RestrictionEvaluator
from app.governance.interceptors.models import InterceptorDecision
from app.governance.interceptors.pre_execution.base import BasePreExecutionInterceptor


class GovernancePreExecutionInterceptor(BasePreExecutionInterceptor):
    name = "governance-pre-execution"

    def __init__(
        self,
        *,
        policy_evaluator: PolicyEvaluator,
        restriction_evaluator: RestrictionEvaluator,
        approval_evaluator: ApprovalEvaluator,
        audit_service: AuditService,
        dif_service: DIFService,
    ) -> None:
        self._policy_evaluator = policy_evaluator
        self._restriction_evaluator = restriction_evaluator
        self._approval_evaluator = approval_evaluator
        self._audit_service = audit_service
        self._dif_service = dif_service

    async def intercept(self, context: GovernanceInterceptorContext) -> InterceptorDecision:
        decision = await self._policy_evaluator.evaluate(context)
        restriction_violations = self._restriction_evaluator.evaluate(context, decision)
        dif_decision = await self._dif_service.evaluate(
            self._policy_evaluator.to_governance_context(context)
        )

        approval_resolution = await self._approval_evaluator.evaluate(
            context,
            decision,
            violation_codes=[violation.code for violation in restriction_violations],
            dif_status=dif_decision.status,
        )

        violations = list(decision.violations)
        violations.extend(violation.message for violation in restriction_violations)
        if dif_decision.status == "block":
            violations.append(dif_decision.reason)

        allowed = decision.allowed and not restriction_violations and dif_decision.status != "block"
        if approval_resolution.status != "not_required":
            allowed = allowed and approval_resolution.status == "approved"

        reason = decision.reason
        if restriction_violations:
            reason = "execution_restricted"
        if dif_decision.status == "block":
            reason = "dif_blocked"
        elif approval_resolution.status not in {"not_required", "approved"}:
            reason = approval_resolution.reason

        final_decision = GovernanceDecision(
            allowed=allowed,
            requires_approval=approval_resolution.status != "not_required",
            reason=reason,
            violations=tuple(violations),
            restrictions=decision.restrictions,
            approval=approval_resolution,
            metadata={
                **decision.metadata,
                "restriction_violations": [
                    {"code": violation.code, "message": violation.message, "metadata": violation.metadata}
                    for violation in restriction_violations
                ],
                "dif_decision": {
                    "status": dif_decision.status,
                    "reason": dif_decision.reason,
                    "metadata": dif_decision.metadata,
                },
                "governance_target": context.target,
                "interception_phase": context.phase,
                "workflow_name": context.workflow_name,
                "user_id": context.user_id,
                "role_names": list(context.role_names),
            },
        )
        audit_record = await self._audit_service.record(
            AuditRecord.create(
                trace_id=context.trace_id,
                event_type=f"governance.intercepted.{context.phase}",
                outcome="allowed" if final_decision.allowed else "blocked",
                reason=final_decision.reason,
                agent_name=context.agent_name,
                conversation_id=context.conversation_id,
                requested_tool=context.requested_tool,
                metadata={
                    **final_decision.metadata,
                    "approval": {
                        "status": final_decision.approval.status if final_decision.approval else None,
                        "reason": final_decision.approval.reason if final_decision.approval else None,
                        "approver": final_decision.approval.approver if final_decision.approval else None,
                    },
                    "restrictions": final_decision.restrictions.as_metadata(),
                    "violations": list(final_decision.violations),
                },
            )
        )
        final_decision = GovernanceDecision(
            allowed=final_decision.allowed,
            requires_approval=final_decision.requires_approval,
            reason=final_decision.reason,
            violations=final_decision.violations,
            restrictions=final_decision.restrictions,
            approval=final_decision.approval,
            audit_record=audit_record,
            metadata=final_decision.metadata,
        )
        return InterceptorDecision(
            allowed=final_decision.allowed,
            phase=InterceptionPhase.PRE_EXECUTION,
            target=context.target,
            governance_decision=final_decision,
            metadata={"interceptor": self.name},
        )


def build_default_pre_execution_interceptor(
    *,
    policy_evaluator: PolicyEvaluator,
    restriction_evaluator: RestrictionEvaluator,
    approval_evaluator: ApprovalEvaluator,
    audit_service: AuditService,
    dif_service: DIFService,
) -> GovernancePreExecutionInterceptor:
    return GovernancePreExecutionInterceptor(
        policy_evaluator=policy_evaluator,
        restriction_evaluator=restriction_evaluator,
        approval_evaluator=approval_evaluator,
        audit_service=audit_service,
        dif_service=dif_service,
    )
