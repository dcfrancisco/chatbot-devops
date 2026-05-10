from app.llm.base import Provider
from app.shared.registry import NamedRegistry


class ProviderRegistry(NamedRegistry[Provider]):
    pass