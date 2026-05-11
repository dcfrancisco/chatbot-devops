from __future__ import annotations

from app.governance.audits import AuditRecord, AuditService
from app.governance.interceptors.context import GovernanceInterceptorContext, InterceptionPhase
from app.governance.interceptors.models import InterceptorOutcome
from app.governance.interceptors.post_execution.base import BasePostExecutionInterceptor


class AuditEnforcementInterceptor(BasePostExecutionInterceptor):
    name = "audit-enforcement-post-execution"

    def __init__(self, audit_service: AuditService) -> None:
        self._audit_service = audit_service

    async def intercept(self, context: GovernanceInterceptorContext) -> InterceptorOutcome:
        await self._audit_service.record(
            AuditRecord.create(
                trace_id=context.trace_id,
                event_type=f"governance.intercepted.{context.phase}",
                outcome="completed",
                reason="post_execution_audited",
                agent_name=context.agent_name,
                conversation_id=context.conversation_id,
                requested_tool=context.requested_tool,
                metadata={
                    **context.metadata,
                    "governance_target": context.target,
                    "interception_phase": context.phase,
                    "workflow_name": context.workflow_name,
                    "user_id": context.user_id,
                    "role_names": list(context.role_names),
                },
            )
        )
        return InterceptorOutcome(
            target=context.target,
            phase=InterceptionPhase.POST_EXECUTION,
            status="audited",
            metadata={"interceptor": self.name},
        )


def build_default_post_execution_interceptor(*, audit_service: AuditService) -> AuditEnforcementInterceptor:
    return AuditEnforcementInterceptor(audit_service)
