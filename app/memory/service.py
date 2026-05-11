from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models import MemoryEntry
from app.memory.episodic.service import EpisodicMemoryService
from app.memory.models import MemoryContext
from app.memory.relevance.service import RelevanceScoringService
from app.memory.semantic.service import SemanticMemoryService
from app.memory.session.service import SessionMemoryService
from app.memory.summarization.service import MemorySummarizationService
from app.llm.base import BaseLLMProvider
from app.observability.service import ObservabilityService
from app.observability.tracing.models import SpanKind


class MemoryService:
    def __init__(self, settings: Settings, llm_provider: BaseLLMProvider, observability_service: ObservabilityService) -> None:
        self._settings = settings
        self._observability_service = observability_service
        self._session_service = SessionMemoryService()
        self._episodic_service = EpisodicMemoryService(llm_provider)
        self._semantic_service = SemanticMemoryService(llm_provider)
        self._summarization_service = MemorySummarizationService(settings, llm_provider)
        self._relevance_service = RelevanceScoringService(
            llm_provider,
            top_k=settings.memory_relevance_top_k,
        )

    async def build_context(
        self,
        session: AsyncSession,
        *,
        conversation_id: str,
        query: str,
    ) -> MemoryContext:
        async with self._observability_service.span(
            "memory.load_recent_messages",
            kind=SpanKind.MEMORY_RETRIEVAL,
            component="memory",
            conversation_id=conversation_id,
        ):
            recent_messages = await self._session_service.load_recent_messages(
                session,
                conversation_id=conversation_id,
                limit=self._settings.conversation_window_size,
            )
        async with self._observability_service.span(
            "memory.load_candidates",
            kind=SpanKind.MEMORY_RETRIEVAL,
            component="memory",
            conversation_id=conversation_id,
        ):
            episodic_memories = await self._episodic_service.list_candidates(session, conversation_id=conversation_id)
            semantic_memories = await self._semantic_service.list_candidates(session, conversation_id=conversation_id)
            summary_memories = await self._summarization_service.list_summaries(session, conversation_id=conversation_id)

        async with self._observability_service.span(
            "memory.rank_relevance",
            kind=SpanKind.MEMORY_RETRIEVAL,
            component="memory",
            candidate_count=len(summary_memories) + len(semantic_memories) + len(episodic_memories),
        ):
            ranked = await self._relevance_service.rank(
                query,
                [*summary_memories, *semantic_memories, *episodic_memories],
            )
        relevant_memories = [match.entry for match in ranked]
        self._observability_service.increment("memory.build_context.calls", memory_count=len(relevant_memories))
        return MemoryContext(
            recent_messages=recent_messages,
            relevant_memories=relevant_memories,
            episodic_memories=episodic_memories,
            semantic_memories=semantic_memories,
            summary_memories=summary_memories,
            relevance_matches=ranked,
        )

    async def remember_user_message(
        self,
        session: AsyncSession,
        *,
        conversation_id: str,
        message_index: int,
        content: str,
    ) -> None:
        await self._episodic_service.remember_user_message(
            session,
            conversation_id=conversation_id,
            message_index=message_index,
            content=content,
        )

    async def remember_semantic_fact(
        self,
        session: AsyncSession,
        *,
        key: str,
        content: str,
        conversation_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> MemoryEntry:
        return await self._semantic_service.remember_fact(
            session,
            key=key,
            content=content,
            conversation_id=conversation_id,
            metadata=metadata,
        )

    async def summarize_conversation(self, session: AsyncSession, *, conversation_id: str) -> MemoryEntry | None:
        return await self._summarization_service.summarize_conversation(session, conversation_id=conversation_id)