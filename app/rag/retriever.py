from dataclasses import dataclass

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models import Document, DocumentChunk, Source
from app.models.api import Citation
from app.services.llm import OpenAICompatibleProvider


@dataclass(slots=True)
class RetrievalResult:
    citations: list[Citation]
    context_blocks: list[str]


class RetrieverService:
    def __init__(self, settings: Settings, llm_provider: OpenAICompatibleProvider) -> None:
        self._settings = settings
        self._llm_provider = llm_provider

    async def search(self, session: AsyncSession, query: str, limit: int | None = None) -> RetrievalResult:
        query_embedding = (await self._llm_provider.embed_texts([query]))[0]
        similarity = DocumentChunk.embedding.cosine_distance(query_embedding)
        statement: Select[tuple[DocumentChunk, Document, Source, float]] = (
            select(DocumentChunk, Document, Source, similarity.label("score"))
            .join(Document, Document.id == DocumentChunk.document_id)
            .join(Source, Source.id == Document.source_ref_id)
            .order_by(similarity)
            .limit(limit or self._settings.retrieval_top_k)
        )
        result = await session.execute(statement)
        rows = result.all()

        citations: list[Citation] = []
        context_blocks: list[str] = []
        for chunk, document, source, score in rows:
            snippet = chunk.content[:320].strip()
            citations.append(
                Citation(
                    document_id=document.id,
                    document_title=document.title,
                    source_id=document.source_id,
                    chunk_id=chunk.id,
                    chunk_index=chunk.chunk_index,
                    snippet=snippet,
                    score=float(score),
                )
            )
            context_blocks.append(
                f"[Source: {document.title} | {document.source_id} | {source.source_key} | chunk {chunk.chunk_index}]\n{chunk.content}"
            )

        return RetrievalResult(citations=citations, context_blocks=context_blocks)
