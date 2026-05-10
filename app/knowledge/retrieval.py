from app.knowledge.base import BaseKnowledgeProvider
from app.rag.retriever import RetrieverService


class RetrievalKnowledgeProvider(BaseKnowledgeProvider):
    name = "semantic-retrieval"
    description = "Semantic retrieval provider backed by pgvector document chunks."
    provider_type = "retrieval"
    capabilities = ("retrieval", "citations", "source-tracking")

    def __init__(self, retriever_service: RetrieverService) -> None:
        self._retriever_service = retriever_service

    def metadata(self) -> dict[str, object]:
        return {
            **super().metadata(),
            "service": self._retriever_service.__class__.__name__,
            "retrieval_strategy": "pgvector-semantic-search",
        }