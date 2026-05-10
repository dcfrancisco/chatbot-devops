from openai import AsyncOpenAI

from app.core.config import Settings
from app.llm.providers.shared import OpenAIStyleProvider


class OllamaProvider(OpenAIStyleProvider):
    def __init__(self, settings: Settings) -> None:
        super().__init__(
            provider_name="ollama",
            chat_model=settings.llm_ollama_chat_model,
            embedding_model=settings.llm_ollama_embedding_model,
            client=AsyncOpenAI(
                base_url=settings.llm_ollama_api_base_url,
                api_key=settings.llm_ollama_api_key,
            ),
            configured=bool(settings.llm_ollama_api_base_url),
            description="Local-first Ollama provider using the OpenAI-compatible API surface.",
            capabilities=("chat", "embeddings", "streaming"),
        )