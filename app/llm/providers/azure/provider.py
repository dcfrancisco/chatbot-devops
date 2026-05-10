from openai import AsyncAzureOpenAI

from app.core.config import Settings
from app.llm.providers.shared import OpenAIStyleProvider


class AzureOpenAIProvider(OpenAIStyleProvider):
    def __init__(self, settings: Settings) -> None:
        super().__init__(
            provider_name="azure",
            chat_model=settings.llm_azure_chat_model,
            embedding_model=settings.llm_azure_embedding_model,
            client=AsyncAzureOpenAI(
                api_key=settings.llm_azure_api_key,
                api_version=settings.llm_azure_api_version,
                azure_endpoint=settings.llm_azure_endpoint,
            ),
            configured=bool(settings.llm_azure_api_key and settings.llm_azure_endpoint),
            description="Azure OpenAI provider using deployment-based chat and embedding routing.",
            capabilities=("chat", "embeddings", "streaming"),
        )