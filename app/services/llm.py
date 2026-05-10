from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.core.config import Settings
from app.models.llm import LLMMessage


class OpenAICompatibleProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = AsyncOpenAI(
            base_url=settings.llm_api_base_url,
            api_key=settings.llm_api_key,
        )

    @property
    def provider_name(self) -> str:
        return self._settings.llm_provider

    @property
    def chat_model(self) -> str:
        return self._settings.llm_chat_model

    @property
    def embedding_model(self) -> str:
        return self._settings.llm_embedding_model

    async def healthcheck(self) -> None:
        await self._client.models.list()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        return [list(item.embedding) for item in response.data]

    async def generate(self, messages: list[LLMMessage]) -> str:
        response = await self._client.chat.completions.create(
            model=self.chat_model,
            temperature=self._settings.llm_temperature,
            max_tokens=self._settings.llm_max_tokens,
            messages=[message.model_dump() for message in messages],
        )
        return response.choices[0].message.content or ""

    async def generate_stream(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self.chat_model,
            temperature=self._settings.llm_temperature,
            max_tokens=self._settings.llm_max_tokens,
            messages=[message.model_dump() for message in messages],
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta
