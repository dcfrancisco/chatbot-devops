from __future__ import annotations

import json
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation, ConversationMessage, MessageCitation
from app.models.api import Citation


class OrchestrationLifecycleService:
    async def get_or_create_conversation(self, session: AsyncSession, conversation_id: str | None) -> Conversation:
        conversation: Conversation | None = None
        if conversation_id:
            conversation = await session.get(Conversation, conversation_id)
        if conversation is None:
            conversation = Conversation(id=str(uuid4()))
            session.add(conversation)
            await session.flush()
        return conversation

    async def store_message(
        self,
        session: AsyncSession,
        *,
        conversation_id: str,
        role: str,
        content: str,
        citations: list[Citation],
        metadata_json: dict[str, object],
    ) -> ConversationMessage:
        current_index = await session.scalar(
            select(ConversationMessage.message_index)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(desc(ConversationMessage.message_index))
            .limit(1)
        )
        message = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_index=(current_index or 0) + 1,
            metadata_json=metadata_json,
        )
        session.add(message)
        await session.flush()
        for citation in citations:
            session.add(
                MessageCitation(
                    message_id=message.id,
                    document_id=citation.document_id,
                    chunk_id=citation.chunk_id,
                    source_id=citation.source_id,
                    score=citation.score,
                    snippet=citation.snippet,
                )
            )
        return message

    async def commit_turn(self, session: AsyncSession) -> None:
        await session.commit()

    def format_sse(self, payload: dict[str, object]) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=True)}\n\n"