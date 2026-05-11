from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.governance.base import GovernanceContext
from app.governance.service import GovernanceService
from app.integrations.jenkins.service import JenkinsService
from app.models.api import IngestDocument, IngestFilesystemSource
from app.orchestration.context import ExecutionContext
from app.rag.ingestion import IngestionService
from app.workflows.engine.engine import WorkflowEngine
from app.workflows.execution import WorkflowCancellationToken, WorkflowExecutionContext, WorkflowRunResult
from app.workflows.registry import WorkflowRegistry
from app.workflows.state import WorkflowRunState


class WorkflowService:
    def __init__(
        self,
        workflow_registry: WorkflowRegistry,
        workflow_engine: WorkflowEngine,
        *,
        jenkins_service: JenkinsService | None = None,
        governance_service: GovernanceService | None = None,
        ingestion_service: IngestionService | None = None,
    ) -> None:
        self._workflow_registry = workflow_registry
        self._workflow_engine = workflow_engine
        self._jenkins_service = jenkins_service
        self._governance_service = governance_service
        self._ingestion_service = ingestion_service
        self._active_tokens: dict[str, WorkflowCancellationToken] = {}
        self._states: dict[str, WorkflowRunState] = {}

    async def run(
        self,
        *,
        workflow_name: str,
        input_data: dict[str, Any],
        session: AsyncSession | None = None,
        execution_context: ExecutionContext | None = None,
        services: dict[str, Any] | None = None,
    ) -> WorkflowRunResult:
        definition = self._workflow_registry.get(workflow_name)
        run_id = str(uuid4())
        token = WorkflowCancellationToken()
        self._active_tokens[run_id] = token

        service_tasks = {**self._default_service_tasks(), **(services or {})}

        async def state_listener(state: WorkflowRunState) -> None:
            self._states[state.run_id] = state

        try:
            result = await self._workflow_engine.execute(
                definition=definition,
                input_data=input_data,
                services=service_tasks,
                execution_context=execution_context,
                session=session,
                cancellation_token=token,
                state_listener=state_listener,
                run_id=run_id,
            )
        finally:
            self._active_tokens.pop(run_id, None)

        self._states[result.state.run_id] = result.state
        return result

    def get_state(self, run_id: str) -> WorkflowRunState | None:
        return self._states.get(run_id)

    def cancel(self, run_id: str, *, reason: str = "cancelled_by_operator") -> bool:
        token = self._active_tokens.get(run_id)
        if token is None:
            return False
        token.cancel(reason)
        return True

    def _default_service_tasks(self) -> dict[str, Any]:
        tasks: dict[str, Any] = {}
        if self._jenkins_service is not None:
            tasks["jenkins_job_diagnostics"] = self._run_jenkins_diagnostics
        if self._governance_service is not None:
            tasks["governance_review"] = self._run_governance_review
        if self._ingestion_service is not None:
            tasks["knowledge_base_ingestion"] = self._run_knowledge_ingestion
        return tasks

    async def _run_jenkins_diagnostics(self, context: WorkflowExecutionContext, _step) -> dict[str, Any]:
        assert self._jenkins_service is not None
        job_name = str(context.input_data.get("job_name") or "")
        if job_name:
            payload = await self._jenkins_service.get_job(name=job_name)
            return {"jenkins_job": payload, "job_name": job_name}
        payload = await self._jenkins_service.list_jobs()
        return {"jenkins_jobs": payload.get("jobs", [])}

    async def _run_governance_review(self, context: WorkflowExecutionContext, step) -> dict[str, Any]:
        assert self._governance_service is not None
        requested_tool = str(step.parameters.get("requested_tool") or context.input_data.get("requested_tool") or "") or None
        decision = await self._governance_service.evaluate(
            GovernanceContext(
                trace_id=context.trace_id,
                agent_name=str(context.input_data.get("agent_name") or context.definition.name),
                conversation_id=context.execution_context.conversation_id if context.execution_context is not None else None,
                message=str(context.input_data.get("message") or context.definition.description),
                requested_tool=requested_tool,
                tool_arguments=dict(context.input_data.get("tool_arguments") or {}),
                metadata={
                    "workflow_name": context.definition.name,
                    "workflow_run_id": context.run_id,
                },
            )
        )
        return {
            "governance_review": {
                "allowed": decision.allowed,
                "requires_approval": decision.requires_approval,
                "reason": decision.reason,
                "violations": list(decision.violations),
            }
        }

    async def _run_knowledge_ingestion(self, context: WorkflowExecutionContext, _step) -> dict[str, Any]:
        assert self._ingestion_service is not None
        if context.session is None:
            raise ValueError("Knowledge ingestion workflows require a database session")

        documents = [IngestDocument(**item) for item in context.input_data.get("documents", [])]
        filesystem_sources = [IngestFilesystemSource(**item) for item in context.input_data.get("filesystem_sources", [])]

        if documents:
            response = await self._ingestion_service.ingest_documents(
                context.session,
                documents,
                incremental=bool(context.input_data.get("incremental", True)),
            )
            return {"ingestion_result": response.model_dump()}
        if filesystem_sources:
            response = await self._ingestion_service.ingest_filesystem_sources(
                context.session,
                filesystem_sources,
                incremental=bool(context.input_data.get("incremental", True)),
            )
            return {"ingestion_result": response.model_dump()}
        raise ValueError("Knowledge ingestion workflow requires documents or filesystem_sources input")