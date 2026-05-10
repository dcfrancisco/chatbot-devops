from __future__ import annotations

from dataclasses import dataclass

from app.agents.registry import AgentRegistry
from app.agents.service import ChatService
from app.core.config import Settings
from app.governance.registry import GovernanceRegistry
from app.governance.service import GovernanceService
from app.integrations.api.service import ApiService
from app.integrations.jenkins.service import JenkinsService
from app.knowledge.registry import KnowledgeRegistry
from app.knowledge.registry import KnowledgeLoaderRegistry, KnowledgeSyncRegistry
from app.knowledge.service import KnowledgeManagementService
from app.llm.registry import ProviderRegistry
from app.llm.base import BaseLLMProvider
from app.memory.service import MemoryService
from app.observability.health import HealthService
from app.observability.service import ObservabilityService
from app.orchestration.service import OrchestrationService
from app.rag.ingestion import IngestionService
from app.rag.retriever import RetrieverService
from app.tools.registry import ToolRegistry
from app.tools.service import ToolExecutionService
from app.workflows.registry import WorkflowRegistry


@dataclass(slots=True)
class RuntimePlatform:
    settings: Settings
    provider_registry: ProviderRegistry
    llm_provider: BaseLLMProvider
    jenkins_service: JenkinsService
    api_service: ApiService
    retriever_service: RetrieverService
    memory_service: MemoryService
    orchestration_service: OrchestrationService
    ingestion_service: IngestionService
    chat_service: ChatService
    tool_registry: ToolRegistry
    tool_execution_service: ToolExecutionService
    health_service: HealthService
    agent_registry: AgentRegistry
    governance_registry: GovernanceRegistry
    governance_service: GovernanceService
    observability_service: ObservabilityService
    workflow_registry: WorkflowRegistry
    knowledge_registry: KnowledgeRegistry
    knowledge_loader_registry: KnowledgeLoaderRegistry
    knowledge_sync_registry: KnowledgeSyncRegistry
    knowledge_service: KnowledgeManagementService

    async def aclose(self) -> None:
        await self.observability_service.aclose()
        await self.provider_registry.aclose()
        await self.governance_service.aclose()
        await self.api_service.aclose()
        await self.jenkins_service.aclose()