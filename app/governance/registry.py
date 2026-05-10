from app.governance.base import BaseGovernanceModule
from app.shared.registry import NamedRegistry


class GovernanceRegistry(NamedRegistry[BaseGovernanceModule]):
    pass