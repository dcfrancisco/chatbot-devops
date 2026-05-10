from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ConversationMessage


class SessionMemoryService:
    async def load_recent_messages(
        self,
        session: AsyncSession,
        *,
        conversation_id: str,
        limit: int,
    ) -> list[ConversationMessage]:
        recent_rows = await session.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(desc(ConversationMessage.created_at))
            .limit(limit)
        )
        return list(reversed(recent_rows.all()))