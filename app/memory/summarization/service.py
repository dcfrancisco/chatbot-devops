from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models import ConversationMessage, MemoryEntry
from app.llm.base import BaseLLMProvider
from app.models.llm import LLMMessage


class MemorySummarizationService:
    def __init__(self, settings: Settings, llm_provider: BaseLLMProvider) -> None:
        self._settings = settings
        self._llm_provider = llm_provider

    async def summarize_conversation(self, session: AsyncSession, *, conversation_id: str) -> MemoryEntry | None:
        recent_rows = await session.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(desc(ConversationMessage.created_at))
            .limit(self._settings.memory_summary_max_messages)
        )
        recent_messages = list(reversed(recent_rows.all()))
        if len(recent_messages) < self._settings.memory_summary_min_messages:
            return None

        transcript = "\n".join(f"{message.role}: {message.content}" for message in recent_messages)
        summary = await self._llm_provider.generate(
            [
                LLMMessage(
                    role="system",
                    content=(
                        "Summarize the conversation into stable, retrieval-friendly memory. "
                        "Keep the summary factual, concise, and useful for future turns."
                    ),
                ),
                LLMMessage(role="user", content=transcript),
            ]
        )
        if not summary.strip():
            return None

        embedding = (await self._llm_provider.embed_texts([summary]))[0]
        entry = MemoryEntry(
            conversation_id=conversation_id,
            memory_type="summary",
            key=f"summary:{conversation_id}",
            content=summary.strip(),
            importance=0.75,
            embedding=embedding,
            metadata_json={"source": "summarization", "message_count": len(recent_messages)},
        )
        session.add(entry)
        return entry

    async def list_summaries(self, session: AsyncSession, *, conversation_id: str) -> list[MemoryEntry]:
        rows = await session.execute(
            select(MemoryEntry)
            .where(MemoryEntry.conversation_id == conversation_id)
            .where(MemoryEntry.memory_type == "summary")
        )
        return rows.scalars().all()