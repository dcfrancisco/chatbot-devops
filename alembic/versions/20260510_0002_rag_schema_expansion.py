"""expand rag schema

Revision ID: 20260510_0002
Revises: 20260510_0001
Create Date: 2026-05-10 00:30:00.000000
"""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


revision = "20260510_0002"
down_revision = "20260510_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    legacy_source_id = str(uuid4())

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "sources",
        sa.Column("source_key", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("uri", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("source_key", name="uq_sources_source_key"),
    )
    op.create_index("ix_sources_source_type", "sources", ["source_type"])
    op.create_index("ix_sources_metadata_json", "sources", ["metadata_json"], postgresql_using="gin")

    bind.execute(
        sa.text(
            """
            INSERT INTO sources (id, source_key, source_type, status, metadata_json)
            VALUES (:id, 'legacy-local', 'legacy', 'active', '{}'::jsonb)
            """
        ),
        {"id": legacy_source_id},
    )

    op.create_table(
        "ingestion_runs",
        sa.Column("source_ref_id", sa.UUID(as_uuid=False), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("documents_seen", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("documents_written", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunks_written", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(["source_ref_id"], ["sources.id"], ondelete="SET NULL", name="fk_ingestion_runs_source_ref_id_sources"),
    )
    op.create_index("ix_ingestion_runs_status_started_at", "ingestion_runs", ["status", "started_at"])
    op.create_index("ix_ingestion_runs_metadata_json", "ingestion_runs", ["metadata_json"], postgresql_using="gin")

    op.add_column("documents", sa.Column("source_ref_id", sa.UUID(as_uuid=False), nullable=True))
    op.add_column("documents", sa.Column("ingestion_run_id", sa.UUID(as_uuid=False), nullable=True))
    op.add_column("documents", sa.Column("mime_type", sa.String(length=100), nullable=False, server_default="text/plain"))
    op.add_column("documents", sa.Column("content_sha256", sa.String(length=128), nullable=True))
    op.alter_column(
        "documents",
        "metadata_json",
        existing_type=sa.JSON(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        postgresql_using="metadata_json::jsonb",
        existing_nullable=False,
    )
    bind.execute(sa.text("UPDATE documents SET source_ref_id = :source_ref_id WHERE source_ref_id IS NULL"), {"source_ref_id": legacy_source_id})
    op.alter_column("documents", "source_ref_id", nullable=False)
    op.create_foreign_key("fk_documents_source_ref_id_sources", "documents", "sources", ["source_ref_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_documents_ingestion_run_id_ingestion_runs", "documents", "ingestion_runs", ["ingestion_run_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_documents_source_ref_id", "documents", ["source_ref_id"])
    op.create_index("ix_documents_ingestion_run_id", "documents", ["ingestion_run_id"])
    op.create_index("ix_documents_metadata_json", "documents", ["metadata_json"], postgresql_using="gin")

    op.add_column("document_chunks", sa.Column("source_ref_id", sa.UUID(as_uuid=False), nullable=True))
    op.add_column("document_chunks", sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("document_chunks", sa.Column("content_sha256", sa.String(length=128), nullable=True))
    op.alter_column(
        "document_chunks",
        "metadata_json",
        existing_type=sa.JSON(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        postgresql_using="metadata_json::jsonb",
        existing_nullable=False,
    )
    bind.execute(
        sa.text(
            """
            UPDATE document_chunks dc
            SET source_ref_id = d.source_ref_id
            FROM documents d
            WHERE dc.document_id = d.id
            """
        )
    )
    op.alter_column("document_chunks", "source_ref_id", nullable=False)
    op.create_foreign_key("fk_document_chunks_source_ref_id_sources", "document_chunks", "sources", ["source_ref_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_document_chunks_source_ref_id", "document_chunks", ["source_ref_id"])
    op.create_index("ix_document_chunks_metadata_json", "document_chunks", ["metadata_json"], postgresql_using="gin")
    op.create_unique_constraint("uq_document_chunks_document_id_chunk_index", "document_chunks", ["document_id", "chunk_index"])
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw "
        "ON document_chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )

    op.alter_column(
        "conversations",
        "metadata_json",
        existing_type=sa.JSON(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        postgresql_using="metadata_json::jsonb",
        existing_nullable=False,
    )
    op.create_index("ix_conversations_metadata_json", "conversations", ["metadata_json"], postgresql_using="gin")

    op.add_column("conversation_messages", sa.Column("message_index", sa.Integer(), nullable=True))
    op.alter_column(
        "conversation_messages",
        "citations",
        existing_type=sa.JSON(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        postgresql_using="citations::jsonb",
        existing_nullable=False,
    )
    op.alter_column(
        "conversation_messages",
        "metadata_json",
        existing_type=sa.JSON(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        postgresql_using="metadata_json::jsonb",
        existing_nullable=False,
    )
    bind.execute(
        sa.text(
            """
            WITH ranked AS (
              SELECT id, ROW_NUMBER() OVER (PARTITION BY conversation_id ORDER BY created_at, id) AS rn
              FROM conversation_messages
            )
            UPDATE conversation_messages cm
            SET message_index = ranked.rn
            FROM ranked
            WHERE cm.id = ranked.id
            """
        )
    )
    op.alter_column("conversation_messages", "message_index", nullable=False)
    op.create_unique_constraint(
        "uq_conversation_messages_conversation_id_message_index",
        "conversation_messages",
        ["conversation_id", "message_index"],
    )
    op.create_index("ix_conversation_messages_metadata_json", "conversation_messages", ["metadata_json"], postgresql_using="gin")

    op.create_table(
        "message_citations",
        sa.Column("message_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("document_chunk_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("citation_rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["conversation_messages.id"], ondelete="CASCADE", name="fk_message_citations_message_id_conversation_messages"),
        sa.ForeignKeyConstraint(["document_chunk_id"], ["document_chunks.id"], ondelete="CASCADE", name="fk_message_citations_document_chunk_id_document_chunks"),
        sa.UniqueConstraint("message_id", "document_chunk_id", name="uq_message_citations_message_id_document_chunk_id"),
    )
    op.create_index("ix_message_citations_message_id_rank", "message_citations", ["message_id", "citation_rank"])

    op.create_table(
        "memory_entries",
        sa.Column("conversation_id", sa.UUID(as_uuid=False), nullable=True),
        sa.Column("memory_type", sa.String(length=50), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("importance", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("embedding", Vector(dim=768), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE", name="fk_memory_entries_conversation_id_conversations"),
    )
    op.create_index("ix_memory_entries_conversation_id_memory_type", "memory_entries", ["conversation_id", "memory_type"])
    op.create_index("ix_memory_entries_metadata_json", "memory_entries", ["metadata_json"], postgresql_using="gin")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_memory_entries_embedding_hnsw "
        "ON memory_entries USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_memory_entries_embedding_hnsw")
    op.drop_index("ix_memory_entries_metadata_json", table_name="memory_entries")
    op.drop_index("ix_memory_entries_conversation_id_memory_type", table_name="memory_entries")
    op.drop_table("memory_entries")

    op.drop_index("ix_message_citations_message_id_rank", table_name="message_citations")
    op.drop_table("message_citations")

    op.drop_constraint("uq_conversation_messages_conversation_id_message_index", "conversation_messages", type_="unique")
    op.drop_index("ix_conversation_messages_metadata_json", table_name="conversation_messages")
    op.drop_column("conversation_messages", "message_index")
    op.alter_column("conversation_messages", "metadata_json", existing_type=postgresql.JSONB(astext_type=sa.Text()), type_=sa.JSON(), postgresql_using="metadata_json::json")
    op.alter_column("conversation_messages", "citations", existing_type=postgresql.JSONB(astext_type=sa.Text()), type_=sa.JSON(), postgresql_using="citations::json")

    op.drop_index("ix_conversations_metadata_json", table_name="conversations")
    op.alter_column("conversations", "metadata_json", existing_type=postgresql.JSONB(astext_type=sa.Text()), type_=sa.JSON(), postgresql_using="metadata_json::json")

    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
    op.drop_constraint("uq_document_chunks_document_id_chunk_index", "document_chunks", type_="unique")
    op.drop_index("ix_document_chunks_metadata_json", table_name="document_chunks")
    op.drop_index("ix_document_chunks_source_ref_id", table_name="document_chunks")
    op.drop_constraint("fk_document_chunks_source_ref_id_sources", "document_chunks", type_="foreignkey")
    op.drop_column("document_chunks", "content_sha256")
    op.drop_column("document_chunks", "token_count")
    op.drop_column("document_chunks", "source_ref_id")
    op.alter_column("document_chunks", "metadata_json", existing_type=postgresql.JSONB(astext_type=sa.Text()), type_=sa.JSON(), postgresql_using="metadata_json::json")

    op.drop_index("ix_documents_metadata_json", table_name="documents")
    op.drop_index("ix_documents_ingestion_run_id", table_name="documents")
    op.drop_index("ix_documents_source_ref_id", table_name="documents")
    op.drop_constraint("fk_documents_ingestion_run_id_ingestion_runs", "documents", type_="foreignkey")
    op.drop_constraint("fk_documents_source_ref_id_sources", "documents", type_="foreignkey")
    op.drop_column("documents", "content_sha256")
    op.drop_column("documents", "mime_type")
    op.drop_column("documents", "ingestion_run_id")
    op.drop_column("documents", "source_ref_id")
    op.alter_column("documents", "metadata_json", existing_type=postgresql.JSONB(astext_type=sa.Text()), type_=sa.JSON(), postgresql_using="metadata_json::json")

    op.drop_index("ix_ingestion_runs_metadata_json", table_name="ingestion_runs")
    op.drop_index("ix_ingestion_runs_status_started_at", table_name="ingestion_runs")
    op.drop_table("ingestion_runs")

    op.drop_index("ix_sources_metadata_json", table_name="sources")
    op.drop_index("ix_sources_source_type", table_name="sources")
    op.drop_table("sources")