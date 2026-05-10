from __future__ import annotations

from app.governance.base import GovernanceContext
from app.governance.dif.base import BaseDIFAdapter
from app.governance.dif.models import DIFDecision


class DIFService:
    def __init__(self, adapter: BaseDIFAdapter) -> None:
        self._adapter = adapter

    async def evaluate(self, context: GovernanceContext) -> DIFDecision:
        return await self._adapter.evaluate(context)