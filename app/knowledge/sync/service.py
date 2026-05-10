from __future__ import annotations

from app.knowledge.registry import KnowledgeSyncRegistry
from app.knowledge.sources.models import KnowledgeSourceDefinition


class KnowledgeSyncService:
    def __init__(self, sync_registry: KnowledgeSyncRegistry) -> None:
        self._sync_registry = sync_registry

    async def sync(self, definition: KnowledgeSourceDefinition) -> KnowledgeSourceDefinition:
        adapter_name = definition.sync_adapter or "noop-sync"
        adapter = self._sync_registry.get(adapter_name)
        return await adapter.sync(definition)