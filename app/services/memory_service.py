from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models import ConversationMessage, MemoryEntry
from app.services.llm import OpenAICompatibleProvider


@dataclass(slots=True)
class MemoryContext:
    recent_messages: list[ConversationMessage]
    relevant_memories: list[MemoryEntry]


class MemoryService:
    def __init__(self, settings: Settings, llm_provider: OpenAICompatibleProvider) -> None:
        self._settings = settings
        self._llm_provider = llm_provider

    async def build_context(
        self,
        session: AsyncSession,
        *,
        conversation_id: str,
        query: str,
    ) -> MemoryContext:
        recent_rows = await session.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(desc(ConversationMessage.created_at))
            .limit(self._settings.conversation_window_size)
        )
        recent_messages = list(reversed(recent_rows.all()))

        relevant_memories: list[MemoryEntry] = []
        memory_rows = await session.execute(
            select(MemoryEntry).where(
                or_(MemoryEntry.conversation_id == conversation_id, MemoryEntry.conversation_id.is_(None))
            )
        )
        candidate_memories = memory_rows.scalars().all()
        if candidate_memories:
            query_embedding = (await self._llm_provider.embed_texts([query]))[0]
            ranked = sorted(
                (
                    memory
                    for memory in candidate_memories
                    if memory.embedding is not None
                ),
                key=lambda memory: self._cosine_distance(query_embedding, memory.embedding or []),
            )
            relevant_memories = ranked[:3]

        return MemoryContext(recent_messages=recent_messages, relevant_memories=relevant_memories)

    async def remember_user_message(
        self,
        session: AsyncSession,
        *,
        conversation_id: str,
        message_index: int,
        content: str,
    ) -> None:
        normalized = content.strip()
        if len(normalized) < 8:
            return

        embedding = (await self._llm_provider.embed_texts([normalized]))[0]
        session.add(
            MemoryEntry(
                conversation_id=conversation_id,
                memory_type="episodic",
                key=f"{conversation_id}:{message_index}",
                content=normalized,
                importance=self._importance(normalized),
                embedding=embedding,
                metadata_json={"source": "conversation", "message_index": message_index},
            )
        )

    def _importance(self, content: str) -> float:
        lowered = content.lower()
        if any(marker in lowered for marker in ("remember", "always", "never", "prefer", "my name is", "call me")):
            return 0.9
        if len(content) > 180:
            return 0.65
        return 0.5

    def _cosine_distance(self, left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 1.0
        dot = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = sum(a * a for a in left) ** 0.5
        right_norm = sum(b * b for b in right) ** 0.5
        if left_norm == 0 or right_norm == 0:
            return 1.0
        return 1 - (dot / (left_norm * right_norm))