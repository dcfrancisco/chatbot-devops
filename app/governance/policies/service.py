from __future__ import annotations

from app.governance.base import GovernanceContext, GovernanceDecision
from app.governance.registry import GovernanceRegistry
from app.governance.restrictions.models import RestrictionSet


class PolicyEngineService:
    def __init__(self, registry: GovernanceRegistry) -> None:
        self._registry = registry

    async def evaluate(self, context: GovernanceContext) -> GovernanceDecision:
        merged_restrictions = RestrictionSet()
        policy_results: list[dict[str, object]] = []
        violations: list[str] = []
        allowed = True
        requires_approval = False

        for entry in self._registry.entries():
            decision = await entry.component.evaluate(context)
            merged_restrictions = merged_restrictions.merge(decision.restrictions)
            violations.extend(decision.violations)
            allowed = allowed and decision.allowed
            requires_approval = requires_approval or decision.requires_approval
            policy_results.append(
                {
                    "name": entry.descriptor.name,
                    "allowed": decision.allowed,
                    "requires_approval": decision.requires_approval,
                    "reason": decision.reason,
                    "violations": list(decision.violations),
                }
            )

        reason = "allowed"
        if not allowed:
            reason = "policy_denied"
        elif requires_approval:
            reason = "policy_requires_approval"

        return GovernanceDecision(
            allowed=allowed,
            requires_approval=requires_approval,
            reason=reason,
            violations=tuple(violations),
            restrictions=merged_restrictions,
            metadata={"policy_results": policy_results},
        )