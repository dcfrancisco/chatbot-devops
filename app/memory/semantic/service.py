from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MemoryEntry
from app.llm.base import BaseLLMProvider


class SemanticMemoryService:
    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        self._llm_provider = llm_provider

    async def list_candidates(self, session: AsyncSession, *, conversation_id: str) -> list[MemoryEntry]:
        rows = await session.execute(
            select(MemoryEntry)
            .where(MemoryEntry.memory_type == "semantic")
            .where(or_(MemoryEntry.conversation_id == conversation_id, MemoryEntry.conversation_id.is_(None)))
        )
        return rows.scalars().all()

    async def remember_fact(
        self,
        session: AsyncSession,
        *,
        key: str,
        content: str,
        conversation_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> MemoryEntry:
        normalized = content.strip()
        embedding = (await self._llm_provider.embed_texts([normalized]))[0]
        entry = MemoryEntry(
            conversation_id=conversation_id,
            memory_type="semantic",
            key=key,
            content=normalized,
            importance=0.8,
            embedding=embedding,
            metadata_json=metadata or {},
        )
        session.add(entry)
        return entry