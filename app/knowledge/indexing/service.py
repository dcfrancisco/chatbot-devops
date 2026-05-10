from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Source
from app.knowledge.registry import KnowledgeLoaderRegistry
from app.knowledge.sources.models import KnowledgeIngestionResult, KnowledgeSourceDefinition
from app.rag.ingestion import IngestionService


class KnowledgeIndexingPipeline:
    def __init__(self, loader_registry: KnowledgeLoaderRegistry, ingestion_service: IngestionService) -> None:
        self._loader_registry = loader_registry
        self._ingestion_service = ingestion_service

    async def ingest_source(self, session: AsyncSession, definition: KnowledgeSourceDefinition) -> KnowledgeIngestionResult:
        loader = self._loader_registry.get(definition.loader_name)
        loaded_source = await loader.load(definition)

        ingested_documents = 0
        ingested_chunks = 0
        skipped_documents = 0
        ingestion_runs: list[str] = []

        if loaded_source.documents:
            response = await self._ingestion_service.ingest_documents(session, loaded_source.documents, incremental=True)
            ingested_documents += response.ingested_documents
            ingested_chunks += response.ingested_chunks
            skipped_documents += response.skipped_documents
            ingestion_runs.extend(response.ingestion_runs)

        if loaded_source.filesystem_sources:
            response = await self._ingestion_service.ingest_filesystem_sources(session, loaded_source.filesystem_sources, incremental=True)
            ingested_documents += response.ingested_documents
            ingested_chunks += response.ingested_chunks
            skipped_documents += response.skipped_documents
            ingestion_runs.extend(response.ingestion_runs)

        await self._annotate_source(session, definition, loaded_source.source_metadata())
        return KnowledgeIngestionResult(
            source_key=definition.source_key,
            loader_name=definition.loader_name,
            source_type=definition.source_type,
            version_checksum=definition.version.checksum if definition.version is not None else None,
            ingested_documents=ingested_documents,
            ingested_chunks=ingested_chunks,
            skipped_documents=skipped_documents,
            ingestion_runs=sorted(set(ingestion_runs)),
        )

    async def _annotate_source(self, session: AsyncSession, definition: KnowledgeSourceDefinition, metadata: dict[str, object]) -> None:
        source = await session.scalar(select(Source).where(Source.source_key == definition.source_key))
        if source is None:
            return
        source.status = "active"
        source.checksum = definition.version.checksum if definition.version is not None else source.checksum
        source.metadata_json = {
            **source.metadata_json,
            **metadata,
            "source_uri": definition.uri,
            "source_version": definition.version.checksum if definition.version is not None else None,
            "source_revision": definition.version.revision if definition.version is not None else None,
        }