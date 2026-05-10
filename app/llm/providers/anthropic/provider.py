from __future__ import annotations

from collections.abc import AsyncIterator

import httpx

from app.core.config import Settings
from app.llm.base import BaseLLMProvider, LLMProviderExecutionError
from app.llm.models import LLMChatRequest, LLMChatResponse, LLMEmbeddingRequest, LLMEmbeddingResponse


class AnthropicProvider(BaseLLMProvider):
    name = "anthropic"
    description = "Anthropic provider for chat completion with fallback-compatible streaming behavior."
    capabilities = ("chat", "streaming")

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.llm_anthropic_api_base_url.rstrip("/"),
            timeout=30.0,
            headers={
                "x-api-key": settings.llm_anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )

    @property
    def provider_name(self) -> str:
        return self.name

    @property
    def chat_model(self) -> str:
        return self._settings.llm_anthropic_chat_model

    @property
    def embedding_model(self) -> str:
        return "unsupported"

    async def aclose(self) -> None:
        await self._client.aclose()

    async def healthcheck(self) -> None:
        payload = {
            "model": self.chat_model,
            "max_tokens": 16,
            "messages": [{"role": "user", "content": "ping"}],
        }
        try:
            response = await self._client.post("/messages", json=payload)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMProviderExecutionError("anthropic healthcheck failed") from exc

    async def chat(self, request: LLMChatRequest) -> LLMChatResponse:
        payload = {
            "model": request.model or self.chat_model,
            "max_tokens": request.max_tokens or self._settings.llm_max_tokens,
            "temperature": request.temperature if request.temperature is not None else self._settings.llm_temperature,
            "messages": [{"role": message.role, "content": message.content} for message in request.messages if message.role != "system"],
            "system": "\n".join(message.content for message in request.messages if message.role == "system") or None,
        }
        try:
            response = await self._client.post("/messages", json=payload)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMProviderExecutionError("anthropic chat request failed") from exc
        body = response.json()
        text = "".join(part.get("text", "") for part in body.get("content", []) if part.get("type") == "text")
        usage = body.get("usage", {})
        return LLMChatResponse(
            provider_name=self.provider_name,
            model=request.model or self.chat_model,
            text=text,
            finish_reason=body.get("stop_reason"),
            usage={key: int(value) for key, value in usage.items() if isinstance(value, (int, float))},
            metadata={"configured": bool(self._settings.llm_anthropic_api_key)},
        )

    async def stream_chat(self, request: LLMChatRequest) -> AsyncIterator[str]:
        response = await self.chat(request)
        if response.text:
            yield response.text

    async def embed(self, request: LLMEmbeddingRequest) -> LLMEmbeddingResponse:
        raise NotImplementedError("Anthropic embeddings are not configured in this runtime")

    def metadata(self) -> dict[str, object]:
        return {
            "description": self.description,
            "provider_name": self.provider_name,
            "chat_model": self.chat_model,
            "embedding_model": self.embedding_model,
            "capabilities": list(self.capabilities),
            "configured": bool(self._settings.llm_anthropic_api_key),
        }