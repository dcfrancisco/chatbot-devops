from __future__ import annotations

from app.governance.interceptors.context import GovernanceInterceptorContext
from app.governance.interceptors.models import InterceptorDecision, InterceptorOutcome
from app.governance.interceptors.post_execution import BasePostExecutionInterceptor
from app.governance.interceptors.pre_execution import BasePreExecutionInterceptor


class GovernanceInterceptionService:
    """Shared interception surface for runtime execution boundaries.

    Example:

        decision = await interception_service.intercept_pre_execution(context)
        if not decision.allowed:
            return decision
        await interception_service.intercept_post_execution(context.with_phase(InterceptionPhase.POST_EXECUTION))
    """

    def __init__(
        self,
        pre_execution_interceptors: list[BasePreExecutionInterceptor] | None = None,
        post_execution_interceptors: list[BasePostExecutionInterceptor] | None = None,
    ) -> None:
        self._pre_execution_interceptors = list(pre_execution_interceptors or [])
        self._post_execution_interceptors = list(post_execution_interceptors or [])

    async def intercept_pre_execution(self, context: GovernanceInterceptorContext) -> InterceptorDecision:
        last_decision: InterceptorDecision | None = None
        for interceptor in self._pre_execution_interceptors:
            last_decision = await interceptor.intercept(context)
            if not last_decision.allowed:
                return last_decision
        if last_decision is None:
            raise RuntimeError("No pre-execution governance interceptors configured")
        return last_decision

    async def intercept_post_execution(self, context: GovernanceInterceptorContext) -> list[InterceptorOutcome]:
        outcomes: list[InterceptorOutcome] = []
        for interceptor in self._post_execution_interceptors:
            outcomes.append(await interceptor.intercept(context))
        return outcomes
