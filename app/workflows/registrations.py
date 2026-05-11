from app.shared.registration import FactoryCatalog, register_factory
from app.workflows.base import BaseWorkflow
from app.workflows.templates import (
    ChatWorkflow,
    DeploymentAnalysisWorkflow,
    GovernanceReviewWorkflow,
    IncidentInvestigationWorkflow,
    JenkinsDiagnosticsWorkflow,
    KnowledgeBaseIngestionWorkflow,
)
from app.workflows.registry import WorkflowRegistry


WORKFLOW_CATALOG = FactoryCatalog[BaseWorkflow]()


@register_factory(WORKFLOW_CATALOG, name="chat-turn", capabilities=("chat", "retrieval", "tools", "memory"), metadata={"kind": "workflow"})
def build_chat_workflow() -> BaseWorkflow:
    return ChatWorkflow()


@register_factory(WORKFLOW_CATALOG, name="incident-investigation", capabilities=("incident", "operations", "approval"), metadata={"kind": "workflow"})
def build_incident_investigation_workflow() -> BaseWorkflow:
    return IncidentInvestigationWorkflow()


@register_factory(WORKFLOW_CATALOG, name="jenkins-diagnostics", capabilities=("jenkins", "operations", "diagnostics"), metadata={"kind": "workflow"})
def build_jenkins_diagnostics_workflow() -> BaseWorkflow:
    return JenkinsDiagnosticsWorkflow()


@register_factory(WORKFLOW_CATALOG, name="deployment-analysis", capabilities=("deployment", "operations", "analysis"), metadata={"kind": "workflow"})
def build_deployment_analysis_workflow() -> BaseWorkflow:
    return DeploymentAnalysisWorkflow()


@register_factory(WORKFLOW_CATALOG, name="governance-review", capabilities=("governance", "review", "approval"), metadata={"kind": "workflow"})
def build_governance_review_workflow() -> BaseWorkflow:
    return GovernanceReviewWorkflow()


@register_factory(WORKFLOW_CATALOG, name="kb-ingestion", capabilities=("knowledge", "ingestion", "operations"), metadata={"kind": "workflow"})
def build_kb_ingestion_workflow() -> BaseWorkflow:
    return KnowledgeBaseIngestionWorkflow()


def build_workflow_registry() -> WorkflowRegistry:
    return WorkflowRegistry(WORKFLOW_CATALOG.build_all())