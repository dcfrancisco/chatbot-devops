from openai import AsyncOpenAI

from app.core.config import Settings
from app.llm.providers.shared import OpenAIStyleProvider


class OpenAIProvider(OpenAIStyleProvider):
    def __init__(self, settings: Settings) -> None:
        super().__init__(
            provider_name="openai",
            chat_model=settings.llm_openai_chat_model,
            embedding_model=settings.llm_openai_embedding_model,
            client=AsyncOpenAI(
                base_url=settings.llm_openai_api_base_url,
                api_key=settings.llm_openai_api_key,
            ),
            configured=bool(settings.llm_openai_api_key),
            description="OpenAI provider for chat, embeddings, and streaming.",
            capabilities=("chat", "embeddings", "streaming"),
        )