from __future__ import annotations

from app.governance.approvals.base import BaseApprovalFlow
from app.governance.approvals.models import ApprovalRequest, ApprovalResolution


class ConfigurableApprovalFlow(BaseApprovalFlow):
    name = "configurable-approval"
    description = "Approval flow that auto-approves or leaves requests pending based on runtime settings."

    def __init__(self, *, auto_approve: bool, approver: str = "system") -> None:
        self._auto_approve = auto_approve
        self._approver = approver

    async def resolve(self, request: ApprovalRequest) -> ApprovalResolution:
        if self._auto_approve:
            return ApprovalResolution(
                status="approved",
                reason="auto_approved_by_configuration",
                approver=self._approver,
                metadata={"approval_flow": self.name, **request.metadata},
            )
        return ApprovalResolution(
            status="pending",
            reason="human_approval_required",
            approver=None,
            metadata={"approval_flow": self.name, **request.metadata},
        )