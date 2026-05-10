from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.core.logging import get_logger
from app.db.models import Document, DocumentChunk, IngestionRun, Source
from app.models.api import IngestDocument, IngestFilesystemSource, IngestResponse
from app.rag.documents import ParsedDocument
from app.rag.parsers import DocumentParser, SUPPORTED_EXTENSIONS
from app.rag.splitters import IntelligentChunker
from app.services.llm import OpenAICompatibleProvider


@dataclass(slots=True)
class IngestionStats:
    ingested_documents: int = 0
    ingested_chunks: int = 0
    skipped_documents: int = 0
    ingestion_runs: list[str] | None = None

    def __post_init__(self) -> None:
        if self.ingestion_runs is None:
            self.ingestion_runs = []


class IngestionService:
    def __init__(self, settings: Settings, llm_provider: OpenAICompatibleProvider) -> None:
        self._settings = settings
        self._llm_provider = llm_provider
        self._parser = DocumentParser()
        self._chunker = IntelligentChunker(settings)
        self._logger = get_logger(__name__)

    async def ingest_documents(
        self,
        session: AsyncSession,
        documents: list[IngestDocument],
        *,
        incremental: bool = True,
    ) -> IngestResponse:
        stats = IngestionStats()
        source_cache: dict[str, Source] = {}
        run_cache: dict[str, IngestionRun] = {}

        try:
            for document in documents:
                source = await self._get_or_create_source(
                    session,
                    source_cache,
                    source_key=document.source_key,
                    source_type=document.source_type,
                    source_uri=document.source_uri,
                    source_metadata={"source_id": document.source_id, **document.metadata},
                )
                ingestion_run = await self._get_or_create_run(session, run_cache, source)
                ingestion_run.documents_seen += 1

                parsed_document = ParsedDocument(
                    source_path=document.source_uri or document.source_id,
                    source_id=document.source_id,
                    source_key=document.source_key,
                    source_type=document.source_type,
                    title=document.title,
                    mime_type=document.mime_type,
                    text=document.text.strip(),
                    checksum=document.content_sha256 or sha256(document.text.encode("utf-8")).hexdigest(),
                    metadata=document.metadata,
                )
                await self._upsert_document(
                    session,
                    source,
                    ingestion_run,
                    parsed_document,
                    stats,
                    incremental=incremental,
                )

            await self._finalize_runs(run_cache.values(), success=True)
            await session.commit()
        except Exception as exc:
            self._logger.exception("document_ingestion_failed")
            await self._finalize_runs(run_cache.values(), success=False, error_text=str(exc))
            await session.commit()
            raise

        return IngestResponse(
            ingested_documents=stats.ingested_documents,
            ingested_chunks=stats.ingested_chunks,
            skipped_documents=stats.skipped_documents,
            ingestion_runs=list(stats.ingestion_runs or []),
        )

    async def ingest_filesystem_sources(
        self,
        session: AsyncSession,
        sources: list[IngestFilesystemSource],
        *,
        incremental: bool = True,
    ) -> IngestResponse:
        stats = IngestionStats()
        source_cache: dict[str, Source] = {}
        run_cache: dict[str, IngestionRun] = {}

        try:
            for source_request in sources:
                source = await self._get_or_create_source(
                    session,
                    source_cache,
                    source_key=source_request.source_key,
                    source_type=source_request.source_type,
                    source_uri=Path(source_request.root_path).expanduser().resolve().as_uri(),
                    source_metadata=source_request.metadata,
                )
                ingestion_run = await self._get_or_create_run(session, run_cache, source)
                parsed_documents = await self._parse_filesystem_source(source_request)
                ingestion_run.documents_seen += len(parsed_documents)

                for parsed_document in parsed_documents:
                    await self._upsert_document(
                        session,
                        source,
                        ingestion_run,
                        parsed_document,
                        stats,
                        incremental=incremental,
                    )

            await self._finalize_runs(run_cache.values(), success=True)
            await session.commit()
        except Exception as exc:
            self._logger.exception("filesystem_ingestion_failed")
            await self._finalize_runs(run_cache.values(), success=False, error_text=str(exc))
            await session.commit()
            raise

        return IngestResponse(
            ingested_documents=stats.ingested_documents,
            ingested_chunks=stats.ingested_chunks,
            skipped_documents=stats.skipped_documents,
            ingestion_runs=list(stats.ingestion_runs or []),
        )

    async def _parse_filesystem_source(self, source: IngestFilesystemSource) -> list[ParsedDocument]:
        root_path = Path(source.root_path).expanduser().resolve()
        if not root_path.exists():
            raise FileNotFoundError(f"Ingestion root path does not exist: {root_path}")

        glob_pattern = source.glob_pattern or self._settings.ingestion_default_glob
        candidate_paths = [
            path
            for path in root_path.glob(glob_pattern)
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        semaphore = asyncio.Semaphore(self._settings.ingestion_max_concurrency)

        async def parse_path(path: Path) -> ParsedDocument:
            async with semaphore:
                parsed = await asyncio.to_thread(self._parser.parse, path, source_key=source.source_key)
                parsed.source_id = f"{source.source_key}:{path.relative_to(root_path).as_posix()}"
                parsed.metadata.update(source.metadata)
                parsed.metadata["root_path"] = root_path.as_posix()
                return parsed

        return await asyncio.gather(*(parse_path(path) for path in sorted(candidate_paths)))

    async def _upsert_document(
        self,
        session: AsyncSession,
        source: Source,
        ingestion_run: IngestionRun,
        parsed_document: ParsedDocument,
        stats: IngestionStats,
        *,
        incremental: bool,
    ) -> None:
        existing = await session.scalar(select(Document).where(Document.source_id == parsed_document.source_id))
        if existing is not None and incremental and existing.content_sha256 == parsed_document.checksum:
            stats.skipped_documents += 1
            ingestion_run.metadata_json = {
                **ingestion_run.metadata_json,
                "skipped_documents": ingestion_run.metadata_json.get("skipped_documents", 0) + 1,
            }
            return

        if existing is not None:
            await session.execute(delete(Document).where(Document.id == existing.id))
            await session.flush()

        db_document = Document(
            source_ref_id=source.id,
            ingestion_run_id=ingestion_run.id,
            source_id=parsed_document.source_id,
            title=parsed_document.title,
            mime_type=parsed_document.mime_type,
            content_sha256=parsed_document.checksum,
            metadata_json=parsed_document.metadata,
        )
        session.add(db_document)
        await session.flush()

        chunks = self._chunker.split(parsed_document)
        embeddings = await self._embed_chunks([chunk.content for chunk in chunks])

        for chunk, embedding in zip(chunks, embeddings, strict=True):
            session.add(
                DocumentChunk(
                    document_id=db_document.id,
                    source_ref_id=source.id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    content_sha256=chunk.checksum,
                    metadata_json=chunk.metadata,
                    embedding=embedding,
                )
            )

        stats.ingested_documents += 1
        stats.ingested_chunks += len(chunks)
        if ingestion_run.id not in stats.ingestion_runs:
            stats.ingestion_runs.append(ingestion_run.id)
        ingestion_run.documents_written += 1
        ingestion_run.chunks_written += len(chunks)

    async def _embed_chunks(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        results: list[list[float]] = []
        batch_size = self._settings.ingestion_batch_size
        for batch_start in range(0, len(texts), batch_size):
            batch = texts[batch_start : batch_start + batch_size]
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self._settings.ingestion_retry_attempts),
                wait=wait_exponential(multiplier=self._settings.ingestion_retry_backoff_seconds, min=1, max=8),
                reraise=True,
            ):
                with attempt:
                    results.extend(await self._llm_provider.embed_texts(batch))
        return results

    async def _get_or_create_source(
        self,
        session: AsyncSession,
        source_cache: dict[str, Source],
        *,
        source_key: str,
        source_type: str,
        source_uri: str | None,
        source_metadata: dict,
    ) -> Source:
        cached = source_cache.get(source_key)
        if cached is not None:
            return cached

        source = await session.scalar(select(Source).where(Source.source_key == source_key))
        if source is None:
            source = Source(
                source_key=source_key,
                source_type=source_type,
                uri=source_uri,
                metadata_json=source_metadata,
            )
            session.add(source)
            await session.flush()
        else:
            source.uri = source_uri or source.uri
            source.source_type = source_type
            source.metadata_json = {**source.metadata_json, **source_metadata}

        source_cache[source_key] = source
        return source

    async def _get_or_create_run(
        self,
        session: AsyncSession,
        run_cache: dict[str, IngestionRun],
        source: Source,
    ) -> IngestionRun:
        cached = run_cache.get(source.source_key)
        if cached is not None:
            return cached

        ingestion_run = IngestionRun(
            source_ref_id=source.id,
            status="running",
            metadata_json={"source_key": source.source_key, "source_type": source.source_type},
        )
        session.add(ingestion_run)
        await session.flush()
        run_cache[source.source_key] = ingestion_run
        return ingestion_run

    async def _finalize_runs(
        self,
        runs: Iterable[IngestionRun],
        *,
        success: bool,
        error_text: str | None = None,
    ) -> None:
        for ingestion_run in runs:
            ingestion_run.status = "completed" if success else "failed"
            ingestion_run.completed_at = datetime.now(timezone.utc)
            if error_text is not None:
                ingestion_run.error_text = error_text
