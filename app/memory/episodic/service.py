from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MemoryEntry
from app.llm.base import BaseLLMProvider


class EpisodicMemoryService:
    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        self._llm_provider = llm_provider

    async def list_candidates(self, session: AsyncSession, *, conversation_id: str) -> list[MemoryEntry]:
        rows = await session.execute(
            select(MemoryEntry)
            .where(MemoryEntry.conversation_id == conversation_id)
            .where(MemoryEntry.memory_type == "episodic")
        )
        return rows.scalars().all()

    async def remember_user_message(
        self,
        session: AsyncSession,
        *,
        conversation_id: str,
        message_index: int,
        content: str,
    ) -> MemoryEntry | None:
        normalized = content.strip()
        if len(normalized) < 8:
            return None

        embedding = (await self._llm_provider.embed_texts([normalized]))[0]
        entry = MemoryEntry(
            conversation_id=conversation_id,
            memory_type="episodic",
            key=f"{conversation_id}:{message_index}",
            content=normalized,
            importance=self._importance(normalized),
            embedding=embedding,
            metadata_json={"source": "conversation", "message_index": message_index},
        )
        session.add(entry)
        return entry

    def _importance(self, content: str) -> float:
        lowered = content.lower()
        if any(marker in lowered for marker in ("remember", "always", "never", "prefer", "my name is", "call me")):
            return 0.9
        if len(content) > 180:
            return 0.65
        return 0.5