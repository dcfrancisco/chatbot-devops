from app.agents.registrations import build_agent_registry
from app.agents.service import ChatService
from app.core.config import Settings
from app.governance.approvals import ApprovalService, ConfigurableApprovalFlow
from app.governance.audits import AuditService, StructuredLogAuditSink
from app.governance.dif import DIFService, NoOpDIFAdapter
from app.governance.policies import PolicyEngineService
from app.governance.registrations import build_governance_registry
from app.governance.restrictions import ExecutionRestrictionService
from app.governance.service import GovernanceService
from app.integrations.api.service import ApiService
from app.integrations.jenkins.service import JenkinsService
from app.knowledge.indexing.service import KnowledgeIndexingPipeline
from app.knowledge.registrations import build_knowledge_registry, build_loader_registry, build_sync_registry
from app.knowledge.service import KnowledgeManagementService
from app.knowledge.sync.service import KnowledgeSyncService
from app.llm.registrations import build_provider_registry
from app.llm.provider import RoutedLLMProvider
from app.memory.service import MemoryService
from app.observability.health import HealthService
from app.observability.logging.service import StructuredLoggingService
from app.observability.metrics.service import MetricsService
from app.observability.service import ObservabilityService
from app.observability.telemetry.examples import OpenTelemetryCompatibleSink, StructuredLogTelemetrySink
from app.observability.telemetry.service import TelemetryService
from app.observability.tracing.service import TracingService
from app.orchestration.runtime import RuntimePlatform
from app.orchestration.service import OrchestrationService
from app.rag.ingestion import IngestionService
from app.rag.retriever import RetrieverService
from app.shared.discovery import load_registration_modules
from app.tools.registrations import build_tool_registry
from app.tools.service import ToolExecutionService
from app.workflows.registrations import build_workflow_registry


ServiceContainer = RuntimePlatform


def build_container(settings: Settings) -> RuntimePlatform:
    load_registration_modules()
    telemetry_sinks = []
    if settings.observability_telemetry_logging_enabled:
        telemetry_sinks.append(StructuredLogTelemetrySink())
    if settings.observability_otel_enabled:
        telemetry_sinks.append(OpenTelemetryCompatibleSink())
    telemetry_service = TelemetryService(telemetry_sinks)
    observability_service = ObservabilityService(
        tracing_service=TracingService(telemetry_service),
        telemetry_service=telemetry_service,
        metrics_service=MetricsService(),
        logging_service=StructuredLoggingService(),
    )
    provider_registry = build_provider_registry(settings=settings)
    llm_provider = RoutedLLMProvider(settings, provider_registry)
    jenkins_service = JenkinsService.from_settings(settings)
    api_service = ApiService.from_settings(settings)
    retriever_service = RetrieverService(settings, llm_provider, observability_service)
    memory_service = MemoryService(settings, llm_provider, observability_service)
    ingestion_service = IngestionService(settings, llm_provider)
    tool_registry = build_tool_registry(
        api_service=api_service,
        jenkins_service=jenkins_service,
        retriever_service=retriever_service,
    )
    tool_execution_service = ToolExecutionService(tool_registry, observability_service)
    governance_registry = build_governance_registry(settings=settings)
    governance_service = GovernanceService(
        settings=settings,
        registry=governance_registry,
        policy_engine=PolicyEngineService(governance_registry),
        restriction_service=ExecutionRestrictionService(),
        approval_service=ApprovalService(
            ConfigurableApprovalFlow(
                auto_approve=settings.governance_auto_approve,
                approver=settings.governance_approver_name,
            )
        ),
        audit_service=AuditService([StructuredLogAuditSink()] if settings.governance_audit_enabled else []),
        dif_service=DIFService(NoOpDIFAdapter()),
    )
    orchestration_service = OrchestrationService(
        settings,
        llm_provider,
        retriever_service,
        memory_service,
        tool_execution_service,
        governance_service,
        observability_service,
    )
    agent_registry = build_agent_registry(orchestration_service=orchestration_service)
    workflow_registry = build_workflow_registry()
    knowledge_registry = build_knowledge_registry(retriever_service=retriever_service)
    knowledge_loader_registry = build_loader_registry(settings=settings)
    knowledge_sync_registry = build_sync_registry(settings=settings)
    knowledge_service = KnowledgeManagementService(
        indexing_pipeline=KnowledgeIndexingPipeline(knowledge_loader_registry, ingestion_service),
        sync_service=KnowledgeSyncService(knowledge_sync_registry),
    )
    chat_service = ChatService(agent_registry, observability_service)
    health_service = HealthService(settings, llm_provider)
    return RuntimePlatform(
        settings=settings,
        provider_registry=provider_registry,
        llm_provider=llm_provider,
        jenkins_service=jenkins_service,
        api_service=api_service,
        retriever_service=retriever_service,
        memory_service=memory_service,
        orchestration_service=orchestration_service,
        ingestion_service=ingestion_service,
        chat_service=chat_service,
        tool_registry=tool_registry,
        tool_execution_service=tool_execution_service,
        health_service=health_service,
        agent_registry=agent_registry,
        governance_registry=governance_registry,
        governance_service=governance_service,
        observability_service=observability_service,
        workflow_registry=workflow_registry,
        knowledge_registry=knowledge_registry,
        knowledge_loader_registry=knowledge_loader_registry,
        knowledge_sync_registry=knowledge_sync_registry,
        knowledge_service=knowledge_service,
    )
