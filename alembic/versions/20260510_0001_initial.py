"""initial schema

Revision ID: 20260510_0001
Revises:
Create Date: 2026-05-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "20260510_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("source_id", name="uq_documents_source_id"),
    )

    op.create_table(
        "document_chunks",
        sa.Column("document_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("embedding", Vector(dim=768), nullable=False),
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE", name="fk_document_chunks_document_id_documents"),
    )
    op.create_index("ix_document_chunks_document_id_chunk_index", "document_chunks", ["document_id", "chunk_index"])

    op.create_table(
        "conversations",
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "conversation_messages",
        sa.Column("conversation_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE", name="fk_conversation_messages_conversation_id_conversations"),
    )
    op.create_index(
        "ix_conversation_messages_conversation_id_created_at",
        "conversation_messages",
        ["conversation_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_conversation_messages_conversation_id_created_at", table_name="conversation_messages")
    op.drop_table("conversation_messages")
    op.drop_table("conversations")
    op.drop_index("ix_document_chunks_document_id_chunk_index", table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_table("documents")
