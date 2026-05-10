from __future__ import annotations

import json

from app.core.config import Settings
from app.llm.models import LLMRouteDecision
from app.llm.registry import ProviderRegistry


class LLMProviderRouter:
    def __init__(self, settings: Settings, provider_registry: ProviderRegistry) -> None:
        self._settings = settings
        self._provider_registry = provider_registry

    def select_chat_candidates(self, preferred: str | None = None) -> list[LLMRouteDecision]:
        return self._select_candidates(
            capability="chat",
            preferred=preferred,
            default_provider=self._settings.llm_default_chat_provider,
            fallback_json=self._settings.llm_chat_fallbacks_json,
        )

    def select_embedding_candidates(self, preferred: str | None = None) -> list[LLMRouteDecision]:
        return self._select_candidates(
            capability="embeddings",
            preferred=preferred,
            default_provider=self._settings.llm_default_embedding_provider,
            fallback_json=self._settings.llm_embedding_fallbacks_json,
        )

    def _select_candidates(
        self,
        *,
        capability: str,
        preferred: str | None,
        default_provider: str,
        fallback_json: str,
    ) -> list[LLMRouteDecision]:
        fallback_names = [str(item) for item in json.loads(fallback_json or "[]")]
        ordered_names: list[str] = []
        for name in [preferred, default_provider, *fallback_names]:
            if name and name not in ordered_names:
                ordered_names.append(name)

        decisions: list[LLMRouteDecision] = []
        for index, name in enumerate(ordered_names):
            if name not in self._provider_registry:
                continue
            descriptor = self._provider_registry.describe(name)
            if capability not in descriptor.capabilities:
                continue
            provider = self._provider_registry.get(name)
            if provider.metadata().get("configured") is False:
                continue
            model = provider.chat_model if capability == "chat" else provider.embedding_model
            decisions.append(
                LLMRouteDecision(
                    capability=capability,
                    provider_name=name,
                    model=model,
                    fallback_index=index,
                    reason="preferred" if index == 0 else "fallback",
                    attempted_providers=list(ordered_names[: index + 1]),
                )
            )
        return decisions