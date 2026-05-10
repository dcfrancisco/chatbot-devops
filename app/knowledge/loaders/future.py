from __future__ import annotations

from app.knowledge.loaders.base import BaseKnowledgeSourceLoader
from app.knowledge.sources.models import KnowledgeSourceDefinition, LoadedKnowledgeSource


class _FutureLoader(BaseKnowledgeSourceLoader):
    async def load(self, definition: KnowledgeSourceDefinition) -> LoadedKnowledgeSource:
        raise NotImplementedError(f"Knowledge source loader '{self.name}' is reserved for future implementation")


class GitRepositoryKnowledgeLoader(_FutureLoader):
    name = "git-repo-loader"
    description = "Placeholder loader for future Git repository knowledge sync and ingestion."
    source_kinds = ("git-repo",)


class ConfluenceKnowledgeLoader(_FutureLoader):
    name = "confluence-loader"
    description = "Placeholder loader for future Confluence knowledge ingestion."
    source_kinds = ("confluence",)


class SharePointKnowledgeLoader(_FutureLoader):
    name = "sharepoint-loader"
    description = "Placeholder loader for future SharePoint knowledge ingestion."
    source_kinds = ("sharepoint",)