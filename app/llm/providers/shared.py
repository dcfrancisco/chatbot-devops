from __future__ import annotations

from abc import ABC
from collections.abc import AsyncIterator

from openai import OpenAIError
from openai import AsyncOpenAI

from app.llm.base import BaseLLMProvider, LLMProviderExecutionError
from app.llm.models import LLMChatRequest, LLMChatResponse, LLMEmbeddingRequest, LLMEmbeddingResponse


class OpenAIStyleProvider(BaseLLMProvider, ABC):
    def __init__(
        self,
        *,
        provider_name: str,
        chat_model: str,
        embedding_model: str,
        client: AsyncOpenAI,
        configured: bool,
        description: str,
        capabilities: tuple[str, ...],
    ) -> None:
        self.name = provider_name
        self.description = description
        self.capabilities = capabilities
        self._provider_name = provider_name
        self._chat_model = chat_model
        self._embedding_model = embedding_model
        self._client = client
        self._configured = configured

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def chat_model(self) -> str:
        return self._chat_model

    @property
    def embedding_model(self) -> str:
        return self._embedding_model

    async def aclose(self) -> None:
        await self._client.aclose()

    async def healthcheck(self) -> None:
        try:
            await self._client.models.list()
        except OpenAIError as exc:
            raise LLMProviderExecutionError(f"{self.provider_name} healthcheck failed") from exc

    async def chat(self, request: LLMChatRequest) -> LLMChatResponse:
        try:
            response = await self._client.chat.completions.create(
                model=request.model or self.chat_model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                messages=[message.model_dump() for message in request.messages],
            )
        except OpenAIError as exc:
            raise LLMProviderExecutionError(f"{self.provider_name} chat request failed") from exc
        choice = response.choices[0]
        usage = response.usage.model_dump() if response.usage is not None else {}
        return LLMChatResponse(
            provider_name=self.provider_name,
            model=request.model or self.chat_model,
            text=choice.message.content or "",
            finish_reason=choice.finish_reason,
            usage={key: int(value) for key, value in usage.items() if isinstance(value, (int, float))},
            metadata={"configured": self._configured},
        )

    async def stream_chat(self, request: LLMChatRequest) -> AsyncIterator[str]:
        try:
            stream = await self._client.chat.completions.create(
                model=request.model or self.chat_model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                messages=[message.model_dump() for message in request.messages],
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield delta
        except OpenAIError as exc:
            raise LLMProviderExecutionError(f"{self.provider_name} streaming request failed") from exc

    async def embed(self, request: LLMEmbeddingRequest) -> LLMEmbeddingResponse:
        try:
            response = await self._client.embeddings.create(
                model=request.model or self.embedding_model,
                input=request.texts,
            )
        except OpenAIError as exc:
            raise LLMProviderExecutionError(f"{self.provider_name} embedding request failed") from exc
        return LLMEmbeddingResponse(
            provider_name=self.provider_name,
            model=request.model or self.embedding_model,
            embeddings=[list(item.embedding) for item in response.data],
            metadata={"configured": self._configured},
        )

    def metadata(self) -> dict[str, object]:
        return {
            "description": self.description,
            "provider_name": self.provider_name,
            "chat_model": self.chat_model,
            "embedding_model": self.embedding_model,
            "capabilities": list(self.capabilities),
            "configured": self._configured,
        }