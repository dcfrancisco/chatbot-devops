from app.integrations.api.service import ApiService
from app.integrations.jenkins.service import JenkinsService
from app.rag.retriever import RetrieverService
from app.shared.registration import FactoryCatalog, register_factory
from app.tools.api import ApiTool
from app.tools.base import Tool
from app.tools.jenkins import JenkinsTool
from app.tools.registry import ToolRegistry
from app.tools.search import SemanticSearchTool


TOOL_CATALOG = FactoryCatalog[Tool]()


@register_factory(TOOL_CATALOG, name="api", capabilities=("api", "integration"), metadata={"kind": "tool"})
def build_api_tool(*, api_service: ApiService) -> Tool:
    return ApiTool(api_service)


@register_factory(TOOL_CATALOG, name="jenkins", capabilities=("jenkins", "ci", "integration"), metadata={"kind": "tool"})
def build_jenkins_tool(*, jenkins_service: JenkinsService) -> Tool:
    return JenkinsTool(jenkins_service)


@register_factory(TOOL_CATALOG, name="semantic_search", capabilities=("search", "retrieval"), metadata={"kind": "tool"})
def build_semantic_search_tool(*, retriever_service: RetrieverService) -> Tool:
    return SemanticSearchTool(retriever_service)


def build_tool_registry(
    *,
    api_service: ApiService,
    jenkins_service: JenkinsService,
    retriever_service: RetrieverService,
) -> ToolRegistry:
    return ToolRegistry(
        TOOL_CATALOG.build_all(
            api_service=api_service,
            jenkins_service=jenkins_service,
            retriever_service=retriever_service,
        )
    )