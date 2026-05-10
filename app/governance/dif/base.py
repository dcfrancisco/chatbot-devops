from __future__ import annotations

from abc import ABC, abstractmethod

from app.governance.base import GovernanceContext
from app.governance.dif.models import DIFDecision


class BaseDIFAdapter(ABC):
    name: str
    description: str

    @abstractmethod
    async def evaluate(self, context: GovernanceContext) -> DIFDecision:
        raise NotImplementedError