from __future__ import annotations

from app.core.config import Settings
from app.governance.base import BaseGovernanceModule, GovernanceContext, GovernanceDecision
from app.governance.restrictions.models import RestrictionSet


class AllowAllGovernanceModule(BaseGovernanceModule):
    name = "allow-all"
    description = "Default governance module that preserves existing runtime behavior."

    async def evaluate(self, context: GovernanceContext) -> GovernanceDecision:
        return GovernanceDecision(
            allowed=True,
            reason="default_allow",
            metadata={"agent_name": context.agent_name},
        )


class ConfiguredRestrictionPolicy(BaseGovernanceModule):
    name = "configured-restrictions"
    description = "Builds runtime governance restrictions from environment-backed settings."

    def __init__(self, restrictions: RestrictionSet) -> None:
        self._restrictions = restrictions

    @classmethod
    def from_settings(cls, settings: Settings) -> ConfiguredRestrictionPolicy:
        return cls(
            RestrictionSet(
                tool_execution_enabled=settings.governance_tool_execution_enabled,
                allowed_tools=_csv_to_tuple(settings.governance_allowed_tools_csv),
                blocked_tools=_csv_to_tuple(settings.governance_blocked_tools_csv),
                approval_required_tools=_csv_to_tuple(settings.governance_approval_required_tools_csv),
                allowed_agents=_csv_to_tuple(settings.governance_allowed_agents_csv),
                max_message_chars=settings.governance_max_message_chars,
            )
        )

    async def evaluate(self, context: GovernanceContext) -> GovernanceDecision:
        return GovernanceDecision(
            allowed=True,
            reason="configured_restrictions_loaded",
            restrictions=self._restrictions,
            metadata={"restrictions": self._restrictions.as_metadata()},
        )


class BlockedTermsPolicy(BaseGovernanceModule):
    name = "blocked-terms"
    description = "Simple enterprise safety policy that blocks configured unsafe or disallowed terms."

    def __init__(self, blocked_terms: tuple[str, ...]) -> None:
        self._blocked_terms = tuple(term.lower() for term in blocked_terms if term)

    @classmethod
    def from_settings(cls, settings: Settings) -> BlockedTermsPolicy:
        return cls(_csv_to_tuple(settings.governance_blocked_terms_csv))

    async def evaluate(self, context: GovernanceContext) -> GovernanceDecision:
        lowered = context.message.lower()
        matched = tuple(term for term in self._blocked_terms if term in lowered)
        if not matched:
            return GovernanceDecision(allowed=True, reason="blocked_terms_clear")
        return GovernanceDecision(
            allowed=False,
            reason="blocked_terms_detected",
            violations=tuple(f"Blocked term detected: {term}" for term in matched),
            metadata={"matched_terms": list(matched)},
        )


def _csv_to_tuple(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())