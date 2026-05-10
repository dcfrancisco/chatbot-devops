from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_session
from app.db.models import Conversation, ConversationMessage, Document, DocumentChunk, MemoryEntry, Source
from app.models.api import (
    ConversationMessageView,
    ConversationSummary,
    KnowledgeBaseDocumentView,
    KnowledgeBaseSourceView,
    MemoryEntryView,
)

router = APIRouter(tags=["dashboard"])


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    limit: int = Query(default=30, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[ConversationSummary]:
    conversation_rows = await session.execute(
        select(
            Conversation.id,
            Conversation.title,
            func.max(ConversationMessage.created_at).label("last_message_at"),
            func.count(ConversationMessage.id).label("message_count"),
        )
        .outerjoin(ConversationMessage, ConversationMessage.conversation_id == Conversation.id)
        .group_by(Conversation.id)
        .order_by(desc(func.max(ConversationMessage.created_at)), desc(Conversation.created_at))
        .limit(limit)
    )
    rows = conversation_rows.all()
    summaries: list[ConversationSummary] = []
    for row in rows:
        preview_row = await session.execute(
            select(ConversationMessage.content)
            .where(ConversationMessage.conversation_id == row.id)
            .order_by(desc(ConversationMessage.created_at))
            .limit(1)
        )
        preview = preview_row.scalar_one_or_none()
        summaries.append(
            ConversationSummary(
                id=row.id,
                title=row.title,
                message_count=int(row.message_count or 0),
                last_message_at=row.last_message_at,
                preview=(preview[:120] + "...") if preview and len(preview) > 120 else preview,
            )
        )
    return summaries


@router.get("/conversations/{conversation_id}/messages", response_model=list[ConversationMessageView])
async def get_conversation_messages(
    conversation_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[ConversationMessageView]:
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    rows = await session.scalars(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at, ConversationMessage.message_index)
    )
    return [
        ConversationMessageView(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
            citations=message.citations,
            metadata=message.metadata_json,
        )
        for message in rows.all()
    ]


@router.get("/conversations/{conversation_id}/memory", response_model=list[MemoryEntryView])
async def get_conversation_memory(
    conversation_id: str,
    limit: int = Query(default=20, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[MemoryEntryView]:
    rows = await session.scalars(
        select(MemoryEntry)
        .where(MemoryEntry.conversation_id == conversation_id)
        .order_by(desc(MemoryEntry.importance), desc(MemoryEntry.last_accessed_at))
        .limit(limit)
    )
    return [
        MemoryEntryView(
            id=memory.id,
            memory_type=memory.memory_type,
            key=memory.key,
            content=memory.content,
            importance=memory.importance,
            last_accessed_at=memory.last_accessed_at,
            metadata=memory.metadata_json,
        )
        for memory in rows.all()
    ]


@router.get("/kb/sources", response_model=list[KnowledgeBaseSourceView])
async def list_kb_sources(session: AsyncSession = Depends(get_session)) -> list[KnowledgeBaseSourceView]:
    rows = await session.execute(
        select(
            Source,
            func.count(func.distinct(Document.id)).label("document_count"),
            func.count(DocumentChunk.id).label("chunk_count"),
            func.max(Document.updated_at).label("updated_at"),
        )
        .outerjoin(Document, Document.source_ref_id == Source.id)
        .outerjoin(DocumentChunk, DocumentChunk.document_id == Document.id)
        .group_by(Source.id)
        .order_by(Source.source_key)
    )
    return [
        KnowledgeBaseSourceView(
            id=source.id,
            source_key=source.source_key,
            source_type=source.source_type,
            uri=source.uri,
            status=source.status,
            document_count=int(document_count or 0),
            chunk_count=int(chunk_count or 0),
            updated_at=updated_at,
        )
        for source, document_count, chunk_count, updated_at in rows.all()
    ]


@router.get("/kb/documents", response_model=list[KnowledgeBaseDocumentView])
async def list_kb_documents(
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> list[KnowledgeBaseDocumentView]:
    rows = await session.execute(
        select(
            Document,
            Source.source_key,
            func.count(DocumentChunk.id).label("chunk_count"),
        )
        .join(Source, Source.id == Document.source_ref_id)
        .outerjoin(DocumentChunk, DocumentChunk.document_id == Document.id)
        .group_by(Document.id, Source.source_key)
        .order_by(desc(Document.updated_at))
        .limit(limit)
    )
    return [
        KnowledgeBaseDocumentView(
            id=document.id,
            source_id=document.source_id,
            title=document.title,
            mime_type=document.mime_type,
            source_key=source_key,
            chunk_count=int(chunk_count or 0),
            updated_at=document.updated_at,
            metadata=document.metadata_json,
        )
        for document, source_key, chunk_count in rows.all()
    ]