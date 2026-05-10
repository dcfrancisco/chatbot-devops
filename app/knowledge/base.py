from abc import ABC


class BaseKnowledgeProvider(ABC):
    name: str
    description: str
    provider_type: str = "knowledge"
    capabilities: tuple[str, ...] = ()

    def metadata(self) -> dict[str, object]:
        return {
            "provider_type": self.provider_type,
            "capabilities": list(self.capabilities),
        }