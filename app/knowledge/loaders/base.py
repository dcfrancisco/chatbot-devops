from __future__ import annotations

from abc import ABC, abstractmethod

from app.knowledge.sources.models import KnowledgeSourceDefinition, LoadedKnowledgeSource


class BaseKnowledgeSourceLoader(ABC):
    name: str
    description: str
    source_kinds: tuple[str, ...] = ()

    @abstractmethod
    async def load(self, definition: KnowledgeSourceDefinition) -> LoadedKnowledgeSource:
        raise NotImplementedError

    def metadata(self) -> dict[str, object]:
        return {
            "description": self.description,
            "source_kinds": list(self.source_kinds),
        }