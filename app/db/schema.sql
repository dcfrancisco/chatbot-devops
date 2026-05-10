CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_key VARCHAR(255) NOT NULL UNIQUE,
    source_type VARCHAR(100) NOT NULL,
    uri TEXT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    checksum VARCHAR(128) NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id UUID PRIMARY KEY,
    source_ref_id UUID NULL REFERENCES sources(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ NULL,
    documents_seen INTEGER NOT NULL DEFAULT 0,
    documents_written INTEGER NOT NULL DEFAULT 0,
    chunks_written INTEGER NOT NULL DEFAULT 0,
    error_text TEXT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_ref_id UUID NOT NULL REFERENCES sources(id) ON DELETE RESTRICT,
    ingestion_run_id UUID NULL REFERENCES ingestion_runs(id) ON DELETE SET NULL,
    source_id VARCHAR(255) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL DEFAULT 'text/plain',
    content_sha256 VARCHAR(128) NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    source_ref_id UUID NOT NULL REFERENCES sources(id) ON DELETE RESTRICT,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    content_sha256 VARCHAR(128) NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding VECTOR(768) NOT NULL,
    CONSTRAINT uq_document_chunks_document_id_chunk_index UNIQUE (document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    title VARCHAR(255) NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_index INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    citations JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_conversation_messages_conversation_id_message_index UNIQUE (conversation_id, message_index)
);

CREATE TABLE IF NOT EXISTS message_citations (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    message_id UUID NOT NULL REFERENCES conversation_messages(id) ON DELETE CASCADE,
    document_chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
    citation_rank INTEGER NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    snippet TEXT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_message_citations_message_id_document_chunk_id UNIQUE (message_id, document_chunk_id)
);

CREATE TABLE IF NOT EXISTS memory_entries (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    conversation_id UUID NULL REFERENCES conversations(id) ON DELETE CASCADE,
    memory_type VARCHAR(50) NOT NULL,
    key VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    importance DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NULL,
    embedding VECTOR(768) NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_sources_source_type ON sources (source_type);
CREATE INDEX IF NOT EXISTS ix_sources_metadata_json ON sources USING gin (metadata_json);
CREATE INDEX IF NOT EXISTS ix_ingestion_runs_status_started_at ON ingestion_runs (status, started_at DESC);
CREATE INDEX IF NOT EXISTS ix_ingestion_runs_metadata_json ON ingestion_runs USING gin (metadata_json);
CREATE INDEX IF NOT EXISTS ix_documents_source_ref_id ON documents (source_ref_id);
CREATE INDEX IF NOT EXISTS ix_documents_ingestion_run_id ON documents (ingestion_run_id);
CREATE INDEX IF NOT EXISTS ix_documents_metadata_json ON documents USING gin (metadata_json);
CREATE INDEX IF NOT EXISTS ix_document_chunks_document_id_chunk_index ON document_chunks (document_id, chunk_index);
CREATE INDEX IF NOT EXISTS ix_document_chunks_source_ref_id ON document_chunks (source_ref_id);
CREATE INDEX IF NOT EXISTS ix_document_chunks_metadata_json ON document_chunks USING gin (metadata_json);
CREATE INDEX IF NOT EXISTS ix_conversations_metadata_json ON conversations USING gin (metadata_json);
CREATE INDEX IF NOT EXISTS ix_conversation_messages_conversation_id_created_at ON conversation_messages (conversation_id, created_at);
CREATE INDEX IF NOT EXISTS ix_conversation_messages_metadata_json ON conversation_messages USING gin (metadata_json);
CREATE INDEX IF NOT EXISTS ix_message_citations_message_id_rank ON message_citations (message_id, citation_rank);
CREATE INDEX IF NOT EXISTS ix_memory_entries_conversation_id_memory_type ON memory_entries (conversation_id, memory_type);
CREATE INDEX IF NOT EXISTS ix_memory_entries_metadata_json ON memory_entries USING gin (metadata_json);

CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw
ON document_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS ix_memory_entries_embedding_hnsw
ON memory_entries USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
