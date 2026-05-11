from __future__ import annotations

from abc import ABC, abstractmethod

from app.governance.interceptors.context import GovernanceInterceptorContext
from app.governance.interceptors.models import InterceptorOutcome


class BasePostExecutionInterceptor(ABC):
    name: str

    @abstractmethod
    async def intercept(self, context: GovernanceInterceptorContext) -> InterceptorOutcome:
        raise NotImplementedError
