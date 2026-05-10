from __future__ import annotations

from app.knowledge.sources.models import KnowledgeSourceDefinition
from app.knowledge.sync.base import BaseKnowledgeSyncAdapter


class NoOpKnowledgeSyncAdapter(BaseKnowledgeSyncAdapter):
    name = "noop-sync"
    description = "Default sync adapter that preserves current local ingestion behavior while keeping the sync seam explicit."
    source_kinds = ("markdown", "yaml", "txt", "pdf", "git-repo", "confluence", "sharepoint")

    async def sync(self, definition: KnowledgeSourceDefinition) -> KnowledgeSourceDefinition:
        return definition