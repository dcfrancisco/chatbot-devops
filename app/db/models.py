from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base, TimestampMixin, UUIDMixin


class Source(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sources"

    source_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    documents: Mapped[list["Document"]] = relationship(back_populates="source")
    ingestion_runs: Mapped[list["IngestionRun"]] = relationship(back_populates="source")

    __table_args__ = (
        Index("ix_sources_source_type", "source_type"),
        Index("ix_sources_metadata_json", "metadata_json", postgresql_using="gin"),
    )


class IngestionRun(UUIDMixin, Base):
    __tablename__ = "ingestion_runs"

    source_ref_id: Mapped[str | None] = mapped_column(
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    documents_seen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    documents_written: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunks_written: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    source: Mapped[Source | None] = relationship(back_populates="ingestion_runs")
    documents: Mapped[list["Document"]] = relationship(back_populates="ingestion_run")

    __table_args__ = (
        Index("ix_ingestion_runs_status_started_at", "status", "started_at"),
        Index("ix_ingestion_runs_metadata_json", "metadata_json", postgresql_using="gin"),
    )


class Document(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    source_ref_id: Mapped[str] = mapped_column(
        ForeignKey("sources.id", ondelete="RESTRICT"),
        nullable=False,
    )
    ingestion_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="text/plain", nullable=False)
    content_sha256: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    source: Mapped[Source] = relationship(back_populates="documents")
    ingestion_run: Mapped[IngestionRun | None] = relationship(back_populates="documents")

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_documents_source_ref_id", "source_ref_id"),
        Index("ix_documents_ingestion_run_id", "ingestion_run_id"),
        Index("ix_documents_metadata_json", "metadata_json", postgresql_using="gin"),
    )


class DocumentChunk(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "document_chunks"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_ref_id: Mapped[str] = mapped_column(
        ForeignKey("sources.id", ondelete="RESTRICT"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content_sha256: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)

    document: Mapped[Document] = relationship(back_populates="chunks")
    message_citations: Mapped[list["MessageCitation"]] = relationship(back_populates="document_chunk")

    __table_args__ = (
        Index("ix_document_chunks_document_id_chunk_index", "document_id", "chunk_index"),
        Index("ix_document_chunks_source_ref_id", "source_ref_id"),
        Index("ix_document_chunks_metadata_json", "metadata_json", postgresql_using="gin"),
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_document_id_chunk_index"),
    )


class Conversation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "conversations"

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ConversationMessage.created_at",
    )
    memory_entries: Mapped[list["MemoryEntry"]] = relationship(back_populates="conversation")

    __table_args__ = (Index("ix_conversations_metadata_json", "metadata_json", postgresql_using="gin"),)


class ConversationMessage(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "conversation_messages"

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_index: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    citation_records: Mapped[list["MessageCitation"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_conversation_messages_conversation_id_created_at", "conversation_id", "created_at"),
        UniqueConstraint("conversation_id", "message_index", name="uq_conversation_messages_conversation_id_message_index"),
        Index("ix_conversation_messages_metadata_json", "metadata_json", postgresql_using="gin"),
    )


class MessageCitation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "message_citations"

    message_id: Mapped[str] = mapped_column(
        ForeignKey("conversation_messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_chunk_id: Mapped[str] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=False,
    )
    citation_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    message: Mapped[ConversationMessage] = relationship(back_populates="citation_records")
    document_chunk: Mapped[DocumentChunk] = relationship(back_populates="message_citations")

    __table_args__ = (
        UniqueConstraint("message_id", "document_chunk_id", name="uq_message_citations_message_id_document_chunk_id"),
        Index("ix_message_citations_message_id_rank", "message_id", "citation_rank"),
    )


class MemoryEntry(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "memory_entries"

    conversation_id: Mapped[str | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=True,
    )
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    last_accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    conversation: Mapped[Conversation | None] = relationship(back_populates="memory_entries")

    __table_args__ = (
        Index("ix_memory_entries_conversation_id_memory_type", "conversation_id", "memory_type"),
        Index("ix_memory_entries_metadata_json", "metadata_json", postgresql_using="gin"),
    )
