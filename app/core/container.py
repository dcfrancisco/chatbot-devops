from dataclasses import dataclass

from app.core.config import Settings
from app.rag.ingestion import IngestionService
from app.rag.retriever import RetrieverService
from app.services.api_service import ApiService
from app.services.chat_service import ChatService
from app.services.health_service import HealthService
from app.services.jenkins_service import JenkinsService
from app.services.llm import OpenAICompatibleProvider
from app.services.memory_service import MemoryService
from app.services.orchestration_service import OrchestrationService
from app.tools.api import ApiTool
from app.tools.jenkins import JenkinsTool
from app.tools.registry import ToolRegistry
from app.tools.search import SemanticSearchTool
from app.tools.service import ToolExecutionService


@dataclass(slots=True)
class ServiceContainer:
    settings: Settings
    llm_provider: OpenAICompatibleProvider
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


def build_container(settings: Settings) -> ServiceContainer:
    llm_provider = OpenAICompatibleProvider(settings)
    jenkins_service = JenkinsService.from_settings(settings)
    api_service = ApiService.from_settings(settings)
    retriever_service = RetrieverService(settings, llm_provider)
    memory_service = MemoryService(settings, llm_provider)
    ingestion_service = IngestionService(settings, llm_provider)
    tool_registry = ToolRegistry(
        tools=[
            SemanticSearchTool(retriever_service),
            JenkinsTool(jenkins_service),
            ApiTool(api_service),
        ]
    )
    tool_execution_service = ToolExecutionService(tool_registry)
    orchestration_service = OrchestrationService(
        settings,
        llm_provider,
        retriever_service,
        memory_service,
        tool_execution_service,
    )
    chat_service = ChatService(orchestration_service)
    health_service = HealthService(settings, llm_provider)
    return ServiceContainer(
        settings=settings,
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
    )
