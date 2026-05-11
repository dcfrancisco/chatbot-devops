from __future__ import annotations

from app.workflows.base import BaseWorkflow
from app.workflows.definitions import WorkflowRetryPolicy, WorkflowStepDefinition


class ChatWorkflow(BaseWorkflow):
    def __init__(self) -> None:
        super().__init__(
            name="chat-turn",
            description="Default deterministic workflow for a single retrieval-first conversational turn.",
            entry_step="capture_request",
            tags=("chat", "retrieval", "tools", "memory"),
            metadata={"kind": "workflow", "category": "conversation"},
            steps=(
                WorkflowStepDefinition(
                    name="capture_request",
                    handler="snapshot_inputs",
                    description="Capture the request payload for deterministic downstream orchestration.",
                    parameters={"output_key": "request"},
                ),
                WorkflowStepDefinition(
                    name="synthesize_summary",
                    handler="synthesize_summary",
                    description="Prepare a compact workflow summary for response synthesis.",
                    terminal=True,
                    parameters={"title": "Chat Turn Summary", "output_key": "workflow_summary"},
                ),
            ),
        )


class IncidentInvestigationWorkflow(BaseWorkflow):
    def __init__(self) -> None:
        super().__init__(
            name="incident-investigation",
            description="Operational workflow for deterministic incident investigation and gated escalation.",
            entry_step="capture_incident_scope",
            tags=("incident", "operations", "approval"),
            metadata={"kind": "workflow", "category": "operations"},
            steps=(
                WorkflowStepDefinition(
                    name="capture_incident_scope",
                    handler="snapshot_inputs",
                    description="Capture incident identifiers, service scope, and current symptoms.",
                    parameters={"include_keys": ["incident_id", "service", "severity", "symptoms"], "output_key": "incident_scope"},
                ),
                WorkflowStepDefinition(
                    name="prepare_incident_summary",
                    handler="synthesize_summary",
                    description="Assemble an initial deterministic incident summary.",
                    parameters={"title": "Incident Investigation", "include_keys": ["incident_scope"], "output_key": "incident_summary"},
                ),
                WorkflowStepDefinition(
                    name="approval_checkpoint",
                    handler="approval_gate",
                    description="Require explicit approval before escalation or remediation.",
                    transitions={"awaiting_approval": None},
                    parameters={"approval_key": "incident_escalation"},
                ),
                WorkflowStepDefinition(
                    name="publish_investigation",
                    handler="synthesize_summary",
                    description="Publish the final incident investigation result.",
                    terminal=True,
                    parameters={"title": "Incident Investigation Finalized", "output_key": "workflow_summary"},
                ),
            ),
        )


class JenkinsDiagnosticsWorkflow(BaseWorkflow):
    def __init__(self) -> None:
        super().__init__(
            name="jenkins-diagnostics",
            description="Operational workflow for deterministic Jenkins job diagnostics.",
            entry_step="capture_job_request",
            tags=("jenkins", "operations", "diagnostics"),
            metadata={"kind": "workflow", "category": "operations"},
            steps=(
                WorkflowStepDefinition(
                    name="capture_job_request",
                    handler="snapshot_inputs",
                    description="Capture Jenkins job selection and operator context.",
                    parameters={"include_keys": ["job_name", "operator_note"], "output_key": "diagnostic_request"},
                ),
                WorkflowStepDefinition(
                    name="inspect_jenkins",
                    handler="service_task",
                    description="Execute deterministic Jenkins diagnostics against the configured Jenkins API.",
                    parameters={"service_name": "jenkins_job_diagnostics"},
                    retry_policy=WorkflowRetryPolicy(max_attempts=2, backoff_seconds=0.5),
                ),
                WorkflowStepDefinition(
                    name="publish_diagnostics",
                    handler="synthesize_summary",
                    description="Summarize Jenkins diagnostic evidence for operators.",
                    terminal=True,
                    parameters={"title": "Jenkins Diagnostics", "include_keys": ["diagnostic_request", "jenkins_job", "jenkins_jobs"], "output_key": "workflow_summary"},
                ),
            ),
        )


class DeploymentAnalysisWorkflow(BaseWorkflow):
    def __init__(self) -> None:
        super().__init__(
            name="deployment-analysis",
            description="Operational workflow for deterministic deployment analysis and rollback readiness review.",
            entry_step="capture_deployment_context",
            tags=("deployment", "operations", "analysis"),
            metadata={"kind": "workflow", "category": "operations"},
            steps=(
                WorkflowStepDefinition(
                    name="capture_deployment_context",
                    handler="snapshot_inputs",
                    description="Capture deployment identifiers, environment, and observed anomalies.",
                    parameters={"include_keys": ["deployment_id", "environment", "change_ticket", "anomalies"], "output_key": "deployment_context"},
                ),
                WorkflowStepDefinition(
                    name="publish_deployment_review",
                    handler="synthesize_summary",
                    description="Produce a deterministic deployment review for operators.",
                    terminal=True,
                    parameters={"title": "Deployment Analysis", "include_keys": ["deployment_context"], "output_key": "workflow_summary"},
                ),
            ),
        )


class GovernanceReviewWorkflow(BaseWorkflow):
    def __init__(self) -> None:
        super().__init__(
            name="governance-review",
            description="Enterprise workflow for deterministic governance review and approval guidance.",
            entry_step="capture_governance_request",
            tags=("governance", "review", "approval"),
            metadata={"kind": "workflow", "category": "governance"},
            steps=(
                WorkflowStepDefinition(
                    name="capture_governance_request",
                    handler="snapshot_inputs",
                    description="Capture policy review intent and tool context.",
                    parameters={"include_keys": ["message", "requested_tool", "tool_arguments", "agent_name"], "output_key": "governance_request"},
                ),
                WorkflowStepDefinition(
                    name="evaluate_governance",
                    handler="service_task",
                    description="Run the governance policy, restriction, DIF, and approval evaluation path.",
                    parameters={"service_name": "governance_review"},
                ),
                WorkflowStepDefinition(
                    name="publish_governance_review",
                    handler="synthesize_summary",
                    description="Publish a deterministic governance review summary.",
                    terminal=True,
                    parameters={"title": "Governance Review", "include_keys": ["governance_request", "governance_review"], "output_key": "workflow_summary"},
                ),
            ),
        )


class KnowledgeBaseIngestionWorkflow(BaseWorkflow):
    def __init__(self) -> None:
        super().__init__(
            name="kb-ingestion",
            description="Operational workflow for deterministic knowledge base ingestion runs.",
            entry_step="capture_ingestion_request",
            tags=("knowledge", "ingestion", "operations"),
            metadata={"kind": "workflow", "category": "knowledge"},
            steps=(
                WorkflowStepDefinition(
                    name="capture_ingestion_request",
                    handler="snapshot_inputs",
                    description="Capture ingestion inputs, filesystem sources, and run mode.",
                    parameters={"include_keys": ["documents", "filesystem_sources", "incremental"], "output_key": "ingestion_request"},
                ),
                WorkflowStepDefinition(
                    name="execute_ingestion",
                    handler="service_task",
                    description="Execute deterministic document or filesystem ingestion.",
                    parameters={"service_name": "knowledge_base_ingestion"},
                    retry_policy=WorkflowRetryPolicy(max_attempts=2, backoff_seconds=1.0),
                ),
                WorkflowStepDefinition(
                    name="publish_ingestion_summary",
                    handler="synthesize_summary",
                    description="Summarize ingestion results for operators and audit.",
                    terminal=True,
                    parameters={"title": "Knowledge Ingestion", "include_keys": ["ingestion_request", "ingestion_result"], "output_key": "workflow_summary"},
                ),
            ),
        )