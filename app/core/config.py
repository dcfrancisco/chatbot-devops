from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = Field(default="local-ai-devops-assistant", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@db:5432/devops_assistant",
        alias="DATABASE_URL",
    )

    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    llm_api_base_url: str = Field(default="http://ollama:11434/v1", alias="LLM_API_BASE_URL")
    llm_api_key: str = Field(default="ollama", alias="LLM_API_KEY")
    llm_chat_model: str = Field(default="llama3.1:8b", alias="LLM_CHAT_MODEL")
    llm_embedding_model: str = Field(default="nomic-embed-text", alias="LLM_EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=768, alias="EMBEDDING_DIMENSIONS")
    llm_temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=1200, alias="LLM_MAX_TOKENS")
    llm_default_chat_provider: str = Field(default="ollama", alias="LLM_DEFAULT_CHAT_PROVIDER")
    llm_default_embedding_provider: str = Field(default="ollama", alias="LLM_DEFAULT_EMBEDDING_PROVIDER")
    llm_chat_fallbacks_json: str = Field(default='["openai", "azure", "anthropic"]', alias="LLM_CHAT_FALLBACKS_JSON")
    llm_embedding_fallbacks_json: str = Field(default='["openai", "azure"]', alias="LLM_EMBEDDING_FALLBACKS_JSON")
    llm_guardrails_max_input_chars: int = Field(default=12000, alias="LLM_GUARDRAILS_MAX_INPUT_CHARS")

    llm_ollama_api_base_url: str = Field(default="http://ollama:11434/v1", alias="LLM_OLLAMA_API_BASE_URL")
    llm_ollama_api_key: str = Field(default="ollama", alias="LLM_OLLAMA_API_KEY")
    llm_ollama_chat_model: str = Field(default="llama3.1:8b", alias="LLM_OLLAMA_CHAT_MODEL")
    llm_ollama_embedding_model: str = Field(default="nomic-embed-text", alias="LLM_OLLAMA_EMBEDDING_MODEL")

    llm_openai_api_base_url: str = Field(default="https://api.openai.com/v1", alias="LLM_OPENAI_API_BASE_URL")
    llm_openai_api_key: str = Field(default="", alias="LLM_OPENAI_API_KEY")
    llm_openai_chat_model: str = Field(default="gpt-4o-mini", alias="LLM_OPENAI_CHAT_MODEL")
    llm_openai_embedding_model: str = Field(default="text-embedding-3-small", alias="LLM_OPENAI_EMBEDDING_MODEL")

    llm_azure_endpoint: str = Field(default="", alias="LLM_AZURE_ENDPOINT")
    llm_azure_api_key: str = Field(default="", alias="LLM_AZURE_API_KEY")
    llm_azure_api_version: str = Field(default="2024-10-21", alias="LLM_AZURE_API_VERSION")
    llm_azure_chat_model: str = Field(default="gpt-4o-mini", alias="LLM_AZURE_CHAT_MODEL")
    llm_azure_embedding_model: str = Field(default="text-embedding-3-small", alias="LLM_AZURE_EMBEDDING_MODEL")

    llm_anthropic_api_base_url: str = Field(default="https://api.anthropic.com/v1", alias="LLM_ANTHROPIC_API_BASE_URL")
    llm_anthropic_api_key: str = Field(default="", alias="LLM_ANTHROPIC_API_KEY")
    llm_anthropic_chat_model: str = Field(default="claude-3-5-sonnet-latest", alias="LLM_ANTHROPIC_CHAT_MODEL")

    retrieval_top_k: int = Field(default=6, alias="RETRIEVAL_TOP_K")
    retrieval_max_chunk_chars: int = Field(default=1200, alias="RETRIEVAL_MAX_CHUNK_CHARS")
    retrieval_chunk_overlap: int = Field(default=150, alias="RETRIEVAL_CHUNK_OVERLAP")
    conversation_window_size: int = Field(default=10, alias="CONVERSATION_WINDOW_SIZE")
    memory_relevance_top_k: int = Field(default=4, alias="MEMORY_RELEVANCE_TOP_K")
    memory_summary_min_messages: int = Field(default=8, alias="MEMORY_SUMMARY_MIN_MESSAGES")
    memory_summary_max_messages: int = Field(default=20, alias="MEMORY_SUMMARY_MAX_MESSAGES")
    ingestion_batch_size: int = Field(default=16, alias="INGESTION_BATCH_SIZE")
    ingestion_retry_attempts: int = Field(default=3, alias="INGESTION_RETRY_ATTEMPTS")
    ingestion_retry_backoff_seconds: float = Field(default=1.0, alias="INGESTION_RETRY_BACKOFF_SECONDS")
    ingestion_default_glob: str = Field(default="**/*", alias="INGESTION_DEFAULT_GLOB")
    ingestion_max_concurrency: int = Field(default=4, alias="INGESTION_MAX_CONCURRENCY")
    tool_execution_timeout_seconds: float = Field(default=15.0, alias="TOOL_EXECUTION_TIMEOUT_SECONDS")
    tool_execution_retry_attempts: int = Field(default=2, alias="TOOL_EXECUTION_RETRY_ATTEMPTS")
    tool_api_integrations_json: str = Field(default="{}", alias="TOOL_API_INTEGRATIONS_JSON")

    governance_enabled: bool = Field(default=True, alias="GOVERNANCE_ENABLED")
    governance_tool_execution_enabled: bool = Field(default=True, alias="GOVERNANCE_TOOL_EXECUTION_ENABLED")
    governance_allowed_tools_csv: str = Field(default="", alias="GOVERNANCE_ALLOWED_TOOLS_CSV")
    governance_blocked_tools_csv: str = Field(default="", alias="GOVERNANCE_BLOCKED_TOOLS_CSV")
    governance_approval_required_tools_csv: str = Field(default="jenkins_build,jenkins_create_job", alias="GOVERNANCE_APPROVAL_REQUIRED_TOOLS_CSV")
    governance_allowed_agents_csv: str = Field(default="", alias="GOVERNANCE_ALLOWED_AGENTS_CSV")
    governance_blocked_terms_csv: str = Field(default="rm -rf,drop database,exfiltrate secret", alias="GOVERNANCE_BLOCKED_TERMS_CSV")
    governance_max_message_chars: int | None = Field(default=8000, alias="GOVERNANCE_MAX_MESSAGE_CHARS")
    governance_auto_approve: bool = Field(default=False, alias="GOVERNANCE_AUTO_APPROVE")
    governance_approver_name: str = Field(default="governance-system", alias="GOVERNANCE_APPROVER_NAME")
    governance_audit_enabled: bool = Field(default=True, alias="GOVERNANCE_AUDIT_ENABLED")
    governance_dif_enabled: bool = Field(default=False, alias="GOVERNANCE_DIF_ENABLED")

    observability_enabled: bool = Field(default=True, alias="OBSERVABILITY_ENABLED")
    observability_telemetry_logging_enabled: bool = Field(default=True, alias="OBSERVABILITY_TELEMETRY_LOGGING_ENABLED")
    observability_metrics_enabled: bool = Field(default=True, alias="OBSERVABILITY_METRICS_ENABLED")
    observability_otel_enabled: bool = Field(default=False, alias="OBSERVABILITY_OTEL_ENABLED")

    jenkins_base_url: str = Field(default="http://jenkins:8080", alias="JENKINS_BASE_URL")
    jenkins_username: str = Field(default="jenkins", alias="JENKINS_USERNAME")
    jenkins_password: str = Field(default="change-me", alias="JENKINS_PASSWORD")
    jenkins_timeout_seconds: float = Field(default=10.0, alias="JENKINS_TIMEOUT_SECONDS")
    jenkins_verify_tls: bool = Field(default=True, alias="JENKINS_VERIFY_TLS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
