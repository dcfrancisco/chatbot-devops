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

    retrieval_top_k: int = Field(default=6, alias="RETRIEVAL_TOP_K")
    retrieval_max_chunk_chars: int = Field(default=1200, alias="RETRIEVAL_MAX_CHUNK_CHARS")
    retrieval_chunk_overlap: int = Field(default=150, alias="RETRIEVAL_CHUNK_OVERLAP")
    conversation_window_size: int = Field(default=10, alias="CONVERSATION_WINDOW_SIZE")
    ingestion_batch_size: int = Field(default=16, alias="INGESTION_BATCH_SIZE")
    ingestion_retry_attempts: int = Field(default=3, alias="INGESTION_RETRY_ATTEMPTS")
    ingestion_retry_backoff_seconds: float = Field(default=1.0, alias="INGESTION_RETRY_BACKOFF_SECONDS")
    ingestion_default_glob: str = Field(default="**/*", alias="INGESTION_DEFAULT_GLOB")
    ingestion_max_concurrency: int = Field(default=4, alias="INGESTION_MAX_CONCURRENCY")
    tool_execution_timeout_seconds: float = Field(default=15.0, alias="TOOL_EXECUTION_TIMEOUT_SECONDS")
    tool_execution_retry_attempts: int = Field(default=2, alias="TOOL_EXECUTION_RETRY_ATTEMPTS")
    tool_api_integrations_json: str = Field(default="{}", alias="TOOL_API_INTEGRATIONS_JSON")

    jenkins_base_url: str = Field(default="http://jenkins:8080", alias="JENKINS_BASE_URL")
    jenkins_username: str = Field(default="jenkins", alias="JENKINS_USERNAME")
    jenkins_password: str = Field(default="change-me", alias="JENKINS_PASSWORD")
    jenkins_timeout_seconds: float = Field(default=10.0, alias="JENKINS_TIMEOUT_SECONDS")
    jenkins_verify_tls: bool = Field(default=True, alias="JENKINS_VERIFY_TLS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
