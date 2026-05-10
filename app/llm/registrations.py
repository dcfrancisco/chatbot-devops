from app.core.config import Settings
from app.llm.base import BaseLLMProvider
from app.llm.providers.anthropic import AnthropicProvider
from app.llm.providers.azure import AzureOpenAIProvider
from app.llm.providers.ollama import OllamaProvider
from app.llm.providers.openai import OpenAIProvider
from app.llm.registry import ProviderRegistry
from app.shared.registration import FactoryCatalog, register_factory


PROVIDER_CATALOG = FactoryCatalog[BaseLLMProvider]()


@register_factory(
    PROVIDER_CATALOG,
    name="ollama",
    capabilities=("chat", "embeddings", "streaming"),
    metadata={"kind": "provider", "provider_type": "llm"},
)
def build_ollama_provider(*, settings: Settings) -> BaseLLMProvider:
    return OllamaProvider(settings)


@register_factory(
    PROVIDER_CATALOG,
    name="openai",
    capabilities=("chat", "embeddings", "streaming"),
    metadata={"kind": "provider", "provider_type": "llm"},
)
def build_openai_provider(*, settings: Settings) -> BaseLLMProvider:
    return OpenAIProvider(settings)


@register_factory(
    PROVIDER_CATALOG,
    name="azure",
    capabilities=("chat", "embeddings", "streaming"),
    metadata={"kind": "provider", "provider_type": "llm"},
)
def build_azure_provider(*, settings: Settings) -> BaseLLMProvider:
    return AzureOpenAIProvider(settings)


@register_factory(
    PROVIDER_CATALOG,
    name="anthropic",
    capabilities=("chat", "streaming"),
    metadata={"kind": "provider", "provider_type": "llm"},
)
def build_anthropic_provider(*, settings: Settings) -> BaseLLMProvider:
    return AnthropicProvider(settings)


def build_provider_registry(*, settings: Settings) -> ProviderRegistry:
    return ProviderRegistry(PROVIDER_CATALOG.build_all(settings=settings))