from __future__ import annotations

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ConversationMessage, MemoryEntry
from app.memory.models import MemoryContext, MemoryMatch


class SessionMemoryReader(Protocol):
    async def load_recent_messages(self, session: AsyncSession, *, conversation_id: str, limit: int) -> list[ConversationMessage]: ...


class EpisodicMemoryStore(Protocol):
    async def remember_user_message(
        self,
        session: AsyncSession,
        *,
        conversation_id: str,
        message_index: int,
        content: str,
    ) -> MemoryEntry | None: ...

    async def list_candidates(self, session: AsyncSession, *, conversation_id: str) -> list[MemoryEntry]: ...


class SemanticMemoryStore(Protocol):
    async def list_candidates(self, session: AsyncSession, *, conversation_id: str) -> list[MemoryEntry]: ...

    async def remember_fact(
        self,
        session: AsyncSession,
        *,
        key: str,
        content: str,
        conversation_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> MemoryEntry: ...


class MemorySummarizer(Protocol):
    async def summarize_conversation(self, session: AsyncSession, *, conversation_id: str) -> MemoryEntry | None: ...


class MemoryRelevanceScorer(Protocol):
    async def rank(self, query: str, candidates: list[MemoryEntry]) -> list[MemoryMatch]: ...


class MemoryContextBuilder(Protocol):
    async def build_context(self, session: AsyncSession, *, conversation_id: str, query: str) -> MemoryContext: ...