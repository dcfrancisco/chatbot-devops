from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.indexing.service import KnowledgeIndexingPipeline
from app.knowledge.sources.models import KnowledgeIngestionResult, KnowledgeSourceDefinition
from app.knowledge.sync.service import KnowledgeSyncService


class KnowledgeManagementService:
    def __init__(self, indexing_pipeline: KnowledgeIndexingPipeline, sync_service: KnowledgeSyncService) -> None:
        self._indexing_pipeline = indexing_pipeline
        self._sync_service = sync_service

    async def ingest_source(self, session: AsyncSession, definition: KnowledgeSourceDefinition) -> KnowledgeIngestionResult:
        synced_definition = await self._sync_service.sync(definition)
        return await self._indexing_pipeline.ingest_source(session, synced_definition)

    async def ingest_sources(
        self,
        session: AsyncSession,
        definitions: list[KnowledgeSourceDefinition],
    ) -> list[KnowledgeIngestionResult]:
        results: list[KnowledgeIngestionResult] = []
        for definition in definitions:
            results.append(await self.ingest_source(session, definition))
        return results