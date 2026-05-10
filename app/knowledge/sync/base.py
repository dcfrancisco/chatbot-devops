from __future__ import annotations

from abc import ABC, abstractmethod

from app.knowledge.sources.models import KnowledgeSourceDefinition


class BaseKnowledgeSyncAdapter(ABC):
    name: str
    description: str
    source_kinds: tuple[str, ...] = ()

    @abstractmethod
    async def sync(self, definition: KnowledgeSourceDefinition) -> KnowledgeSourceDefinition:
        raise NotImplementedError

    def metadata(self) -> dict[str, object]:
        return {
            "description": self.description,
            "source_kinds": list(self.source_kinds),
        }