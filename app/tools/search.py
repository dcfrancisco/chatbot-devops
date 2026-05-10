from pydantic import BaseModel, Field

from app.rag.retriever import RetrieverService
from app.tools.base import Tool, ToolExecutionContext


class SemanticSearchArguments(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class SemanticSearchTool(Tool[SemanticSearchArguments]):
    name = "semantic_search"
    description = "Search ingested DevOps knowledge using semantic similarity."
    tags = ("search", "rag")
    arguments_model = SemanticSearchArguments

    def __init__(self, retriever_service: RetrieverService) -> None:
        self._retriever_service = retriever_service

    async def execute(self, context: ToolExecutionContext, arguments: SemanticSearchArguments) -> dict[str, object]:
        retrieval = await self._retriever_service.search(context.session, arguments.query, limit=arguments.limit)
        return {
            "query": arguments.query,
            "limit": arguments.limit,
            "citations": [citation.model_dump() for citation in retrieval.citations],
            "context": retrieval.context_blocks,
        }