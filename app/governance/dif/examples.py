from __future__ import annotations

from app.governance.base import GovernanceContext
from app.governance.dif.base import BaseDIFAdapter
from app.governance.dif.models import DIFDecision


class NoOpDIFAdapter(BaseDIFAdapter):
    name = "noop-dif"
    description = "Placeholder DIF adapter that preserves the extension seam for future enterprise integration."

    async def evaluate(self, context: GovernanceContext) -> DIFDecision:
        return DIFDecision(status="pass", reason="dif_not_configured", metadata={"agent_name": context.agent_name})