from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.llm.models import LLMChatRequest, LLMChatResponse, LLMEmbeddingRequest, LLMEmbeddingResponse
from app.models.llm import LLMMessage


class LLMProviderExecutionError(RuntimeError):
    pass


class BaseLLMProvider(ABC):
    name: str
    description: str
    capabilities: tuple[str, ...] = ()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def chat_model(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def embedding_model(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def healthcheck(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def chat(self, request: LLMChatRequest) -> LLMChatResponse:
        raise NotImplementedError

    @abstractmethod
    async def stream_chat(self, request: LLMChatRequest) -> AsyncIterator[str]:
        raise NotImplementedError

    @abstractmethod
    async def embed(self, request: LLMEmbeddingRequest) -> LLMEmbeddingResponse:
        raise NotImplementedError

    async def aclose(self) -> None:
        return None

    async def generate(self, messages: list[LLMMessage]) -> str:
        response = await self.chat(LLMChatRequest(messages=messages))
        return response.text

    async def generate_stream(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        async for token in self.stream_chat(LLMChatRequest(messages=messages)):
            yield token

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = await self.embed(LLMEmbeddingRequest(texts=texts))
        return response.embeddings

    def metadata(self) -> dict[str, object]:
        return {
            "description": self.description,
            "provider_name": self.provider_name,
            "chat_model": self.chat_model,
            "embedding_model": self.embedding_model,
            "capabilities": list(self.capabilities),
        }


Provider = BaseLLMProvider