from __future__ import annotations

from collections.abc import AsyncIterator

from app.core.config import Settings
from app.llm.base import BaseLLMProvider, LLMProviderExecutionError
from app.llm.guardrails.service import LLMGuardrailsService
from app.llm.models import LLMChatRequest, LLMChatResponse, LLMEmbeddingRequest, LLMEmbeddingResponse
from app.llm.prompts.service import PromptAssemblyFlow
from app.llm.registry import ProviderRegistry
from app.llm.routing.service import LLMProviderRouter
from app.models.llm import LLMMessage


class RoutedLLMProvider(BaseLLMProvider):
    name = "routed-llm"
    description = "Configurable routed LLM facade with provider isolation, fallback support, and guardrails."
    capabilities = ("chat", "embeddings", "streaming", "routing", "fallback")

    def __init__(self, settings: Settings, provider_registry: ProviderRegistry) -> None:
        self._settings = settings
        self._provider_registry = provider_registry
        self._router = LLMProviderRouter(settings, provider_registry)
        self._guardrails = LLMGuardrailsService(max_input_chars=settings.llm_guardrails_max_input_chars)
        self._prompt_flow = PromptAssemblyFlow()

    @property
    def provider_name(self) -> str:
        return self._settings.llm_default_chat_provider

    @property
    def chat_model(self) -> str:
        candidates = self._router.select_chat_candidates()
        return candidates[0].model if candidates else self._settings.llm_chat_model

    @property
    def embedding_model(self) -> str:
        candidates = self._router.select_embedding_candidates()
        return candidates[0].model if candidates else self._settings.llm_embedding_model

    async def healthcheck(self) -> None:
        candidates = self._router.select_chat_candidates()
        if not candidates:
            raise RuntimeError("No configured chat providers are available")
        provider = self._provider_registry.get(candidates[0].provider_name)
        await provider.healthcheck()

    async def chat(self, request: LLMChatRequest) -> LLMChatResponse:
        guarded_request = self._guardrails.validate_chat_request(request)
        last_error: LLMProviderExecutionError | None = None
        preferred_provider = guarded_request.metadata.get("provider") if guarded_request.metadata else None
        for decision in self._router.select_chat_candidates(preferred=str(preferred_provider) if preferred_provider else None):
            provider = self._provider_registry.get(decision.provider_name)
            try:
                response = await provider.chat(guarded_request.model_copy(update={"model": guarded_request.model or decision.model}))
                return self._guardrails.validate_chat_response(
                    response.model_copy(update={"metadata": {**response.metadata, "route": decision.model_dump()}})
                )
            except LLMProviderExecutionError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise RuntimeError("No configured chat providers are available")

    async def stream_chat(self, request: LLMChatRequest) -> AsyncIterator[str]:
        guarded_request = self._guardrails.validate_chat_request(request)
        last_error: LLMProviderExecutionError | None = None
        preferred_provider = guarded_request.metadata.get("provider") if guarded_request.metadata else None
        for decision in self._router.select_chat_candidates(preferred=str(preferred_provider) if preferred_provider else None):
            provider = self._provider_registry.get(decision.provider_name)
            try:
                async for token in provider.stream_chat(guarded_request.model_copy(update={"model": guarded_request.model or decision.model})):
                    yield token
                return
            except LLMProviderExecutionError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise RuntimeError("No configured streaming chat providers are available")

    async def embed(self, request: LLMEmbeddingRequest) -> LLMEmbeddingResponse:
        guarded_request = self._guardrails.validate_embedding_request(request)
        last_error: LLMProviderExecutionError | None = None
        preferred_provider = guarded_request.metadata.get("provider") if guarded_request.metadata else None
        for decision in self._router.select_embedding_candidates(preferred=str(preferred_provider) if preferred_provider else None):
            provider = self._provider_registry.get(decision.provider_name)
            try:
                response = await provider.embed(guarded_request.model_copy(update={"model": guarded_request.model or decision.model}))
                return response.model_copy(update={"metadata": {**response.metadata, "route": decision.model_dump()}})
            except LLMProviderExecutionError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise RuntimeError("No configured embedding providers are available")

    async def generate(self, messages: list[LLMMessage]) -> str:
        request = self._prompt_flow.build_chat_request(
            messages=messages,
            model=None,
            temperature=self._settings.llm_temperature,
            max_tokens=self._settings.llm_max_tokens,
        )
        response = await self.chat(request)
        return response.text

    async def generate_stream(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        request = self._prompt_flow.build_chat_request(
            messages=messages,
            model=None,
            temperature=self._settings.llm_temperature,
            max_tokens=self._settings.llm_max_tokens,
        )
        async for token in self.stream_chat(request):
            yield token

    def metadata(self) -> dict[str, object]:
        return {
            "description": self.description,
            "provider_name": self.provider_name,
            "chat_model": self.chat_model,
            "embedding_model": self.embedding_model,
            "capabilities": list(self.capabilities),
            "configured_providers": [entry.descriptor.name for entry in self._provider_registry.entries()],
        }


OpenAICompatibleProvider = RoutedLLMProvider