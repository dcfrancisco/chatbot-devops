from __future__ import annotations

from abc import ABC, abstractmethod

from app.governance.approvals.models import ApprovalRequest, ApprovalResolution


class BaseApprovalFlow(ABC):
    name: str
    description: str

    @abstractmethod
    async def resolve(self, request: ApprovalRequest) -> ApprovalResolution:
        raise NotImplementedError