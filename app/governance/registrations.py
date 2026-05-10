from app.core.config import Settings
from app.governance.base import BaseGovernanceModule
from app.governance.defaults import AllowAllGovernanceModule, BlockedTermsPolicy, ConfiguredRestrictionPolicy
from app.governance.registry import GovernanceRegistry
from app.shared.registration import FactoryCatalog, register_factory


GOVERNANCE_CATALOG = FactoryCatalog[BaseGovernanceModule]()


@register_factory(
    GOVERNANCE_CATALOG,
    name="allow-all",
    capabilities=("fallback",),
    metadata={"kind": "governance", "module_type": "policy"},
)
def build_allow_all_policy(*, settings: Settings) -> BaseGovernanceModule:
    return AllowAllGovernanceModule()


@register_factory(
    GOVERNANCE_CATALOG,
    name="configured-restrictions",
    capabilities=("restrictions", "tool-governance"),
    metadata={"kind": "governance", "module_type": "policy"},
)
def build_configured_restrictions_policy(*, settings: Settings) -> BaseGovernanceModule:
    return ConfiguredRestrictionPolicy.from_settings(settings)


@register_factory(
    GOVERNANCE_CATALOG,
    name="blocked-terms",
    capabilities=("safety", "message-validation"),
    metadata={"kind": "governance", "module_type": "policy"},
)
def build_blocked_terms_policy(*, settings: Settings) -> BaseGovernanceModule:
    return BlockedTermsPolicy.from_settings(settings)


def build_governance_registry(*, settings: Settings) -> GovernanceRegistry:
    modules = GOVERNANCE_CATALOG.build_all(settings=settings)
    if settings.governance_enabled:
        active = [module for module in modules if module.name != "allow-all"]
        return GovernanceRegistry(active or [AllowAllGovernanceModule()])
    return GovernanceRegistry([AllowAllGovernanceModule()])