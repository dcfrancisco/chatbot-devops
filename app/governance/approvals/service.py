from __future__ import annotations

from app.governance.approvals.base import BaseApprovalFlow
from app.governance.approvals.models import ApprovalRequest, ApprovalResolution


class ApprovalService:
    def __init__(self, approval_flow: BaseApprovalFlow) -> None:
        self._approval_flow = approval_flow

    async def resolve(self, request: ApprovalRequest) -> ApprovalResolution:
        return await self._approval_flow.resolve(request)