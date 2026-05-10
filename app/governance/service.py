from __future__ import annotations

from app.core.config import Settings
from app.governance.approvals import ApprovalRequest, ApprovalResolution, ApprovalService
from app.governance.audits import AuditRecord, AuditService
from app.governance.base import GovernanceContext, GovernanceDecision
from app.governance.dif import DIFService
from app.governance.policies import PolicyEngineService
from app.governance.registry import GovernanceRegistry
from app.governance.restrictions import ExecutionRestrictionService, RestrictionViolation


class GovernanceService:
    def __init__(
        self,
        settings: Settings,
        registry: GovernanceRegistry,
        policy_engine: PolicyEngineService,
        restriction_service: ExecutionRestrictionService,
        approval_service: ApprovalService,
        audit_service: AuditService,
        dif_service: DIFService,
    ) -> None:
        self._settings = settings
        self._registry = registry
        self._policy_engine = policy_engine
        self._restriction_service = restriction_service
        self._approval_service = approval_service
        self._audit_service = audit_service
        self._dif_service = dif_service

    async def evaluate(self, context: GovernanceContext) -> GovernanceDecision:
        policy_decision = await self._policy_engine.evaluate(context)
        restriction_violations = self._restriction_service.validate(context, policy_decision.restrictions)
        dif_decision = await self._dif_service.evaluate(context)

        approval_required = policy_decision.requires_approval
        if context.requested_tool and context.requested_tool in policy_decision.restrictions.approval_required_tools:
            approval_required = True
        if dif_decision.status == "review":
            approval_required = True

        approval_resolution = ApprovalResolution(status="not_required", reason="not_required")
        if approval_required:
            approval_resolution = await self._approval_service.resolve(
                ApprovalRequest(
                    trace_id=context.trace_id,
                    agent_name=context.agent_name,
                    conversation_id=context.conversation_id,
                    requested_tool=context.requested_tool,
                    reason=policy_decision.reason,
                    metadata={
                        "violations": [violation.code for violation in restriction_violations],
                        "dif_status": dif_decision.status,
                    },
                )
            )

        violations = list(policy_decision.violations)
        violations.extend(violation.message for violation in restriction_violations)
        if dif_decision.status == "block":
            violations.append(dif_decision.reason)

        allowed = policy_decision.allowed and not restriction_violations and dif_decision.status != "block"
        if approval_required:
            allowed = allowed and approval_resolution.status == "approved"

        reason = policy_decision.reason
        if restriction_violations:
            reason = "execution_restricted"
        if dif_decision.status == "block":
            reason = "dif_blocked"
        elif approval_required and approval_resolution.status != "approved":
            reason = approval_resolution.reason

        decision = GovernanceDecision(
            allowed=allowed,
            requires_approval=approval_required,
            reason=reason,
            violations=tuple(violations),
            restrictions=policy_decision.restrictions,
            approval=approval_resolution,
            metadata={
                **policy_decision.metadata,
                "restriction_violations": [self._serialize_violation(violation) for violation in restriction_violations],
                "dif_decision": {
                    "status": dif_decision.status,
                    "reason": dif_decision.reason,
                    "metadata": dif_decision.metadata,
                },
            },
        )
        audit_record = await self._audit_service.record(
            AuditRecord.create(
                trace_id=context.trace_id,
                event_type="governance.evaluated",
                outcome="allowed" if decision.allowed else "blocked",
                reason=decision.reason,
                agent_name=context.agent_name,
                conversation_id=context.conversation_id,
                requested_tool=context.requested_tool,
                metadata={
                    **decision.metadata,
                    "approval": {
                        "status": decision.approval.status if decision.approval else None,
                        "reason": decision.approval.reason if decision.approval else None,
                        "approver": decision.approval.approver if decision.approval else None,
                    },
                    "restrictions": decision.restrictions.as_metadata(),
                    "violations": list(decision.violations),
                },
            )
        )
        return GovernanceDecision(
            allowed=decision.allowed,
            requires_approval=decision.requires_approval,
            reason=decision.reason,
            violations=decision.violations,
            restrictions=decision.restrictions,
            approval=decision.approval,
            audit_record=audit_record,
            metadata=decision.metadata,
        )

    async def aclose(self) -> None:
        await self._audit_service.aclose()

    def _serialize_violation(self, violation: RestrictionViolation) -> dict[str, object]:
        return {
            "code": violation.code,
            "message": violation.message,
            "metadata": violation.metadata,
        }