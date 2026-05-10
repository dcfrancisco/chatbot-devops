from datetime import datetime
from typing import Any
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Citation(BaseModel):
    document_id: str
    document_title: str
    source_id: str
    chunk_id: str
    chunk_index: int
    snippet: str
    score: float


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
    agent_name: str | None = Field(default=None, min_length=1)
    stream: bool = False


class ToolInvocationSummary(BaseModel):
    name: str
    status: Literal["success", "error", "timeout"]
    trace_id: str


class GovernanceSummary(BaseModel):
    allowed: bool
    reason: str
    requires_approval: bool = False
    requested_tool: str | None = None
    approval_status: str | None = None
    audit_record_id: str | None = None
    violations: list[str] = Field(default_factory=list)


class OrchestrationMetadata(BaseModel):
    trace_id: str
    retrieval_count: int = 0
    memory_count: int = 0
    tool_invocation: ToolInvocationSummary | None = None
    governance: GovernanceSummary | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    citations: list[Citation]
    provider: str
    model: str
    orchestration: OrchestrationMetadata | None = None


class IngestDocument(BaseModel):
    source_id: str = Field(min_length=1)
    source_key: str = Field(default="default", min_length=1)
    source_type: str = Field(default="manual", min_length=1)
    source_uri: str | None = None
    mime_type: str = Field(default="text/plain", min_length=1)
    content_sha256: str | None = None
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestFilesystemSource(BaseModel):
    source_key: str = Field(min_length=1)
    root_path: str = Field(min_length=1)
    glob_pattern: str = Field(default="**/*")
    source_type: str = Field(default="filesystem", min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestRequest(BaseModel):
    documents: list[IngestDocument] = Field(default_factory=list)
    filesystem_sources: list[IngestFilesystemSource] = Field(default_factory=list)
    incremental: bool = True

    @model_validator(mode="after")
    def validate_non_empty(self) -> "IngestRequest":
        if not self.documents and not self.filesystem_sources:
            raise ValueError("At least one document or filesystem source is required")
        return self


class IngestResponse(BaseModel):
    ingested_documents: int
    ingested_chunks: int
    skipped_documents: int = 0
    ingestion_runs: list[str] = Field(default_factory=list)


class ToolDescriptor(BaseModel):
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    timeout_seconds: float
    retry_attempts: int
    safe_execution: bool = True
    input_schema: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolExecutionRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolExecutionError(BaseModel):
    code: str
    message: str
    retryable: bool = False


class ToolExecutionTrace(BaseModel):
    trace_id: str
    started_at: datetime
    completed_at: datetime
    duration_ms: int
    attempts: int
    timeout_seconds: float


class ToolExecutionResponse(BaseModel):
    name: str
    status: Literal["success", "error", "timeout"]
    data: dict[str, Any] | None = None
    error: ToolExecutionError | None = None
    trace: ToolExecutionTrace


class ConversationSummary(BaseModel):
    id: str
    title: str | None = None
    message_count: int = 0
    last_message_at: datetime | None = None
    preview: str | None = None


class ConversationMessageView(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    citations: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryEntryView(BaseModel):
    id: str
    memory_type: str
    key: str
    content: str
    importance: float
    last_accessed_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeBaseSourceView(BaseModel):
    id: str
    source_key: str
    source_type: str
    uri: str | None = None
    status: str
    document_count: int = 0
    chunk_count: int = 0
    updated_at: datetime | None = None


class KnowledgeBaseDocumentView(BaseModel):
    id: str
    source_id: str
    title: str
    mime_type: str
    source_key: str
    chunk_count: int = 0
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    database: str
    llm_provider: str
    llm_model: str
    embedding_model: str
    tools: int
