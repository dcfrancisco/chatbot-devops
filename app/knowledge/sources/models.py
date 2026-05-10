from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from app.models.api import IngestDocument, IngestFilesystemSource


@dataclass(slots=True, frozen=True)
class SourceVersion:
    revision: str
    checksum: str
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True, frozen=True)
class KnowledgeSourceDefinition:
    source_key: str
    source_type: str
    uri: str
    loader_name: str
    display_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    version: SourceVersion | None = None
    sync_adapter: str | None = None

    @classmethod
    def create(
        cls,
        *,
        source_key: str,
        source_type: str,
        uri: str,
        loader_name: str,
        display_name: str | None = None,
        metadata: dict[str, Any] | None = None,
        revision: str | None = None,
        sync_adapter: str | None = None,
    ) -> KnowledgeSourceDefinition:
        normalized_metadata = metadata or {}
        version_seed = "|".join([source_key, source_type, uri, loader_name, revision or "default"])
        return cls(
            source_key=source_key,
            source_type=source_type,
            uri=uri,
            loader_name=loader_name,
            display_name=display_name,
            metadata=normalized_metadata,
            version=SourceVersion(
                revision=revision or "default",
                checksum=sha256(version_seed.encode("utf-8")).hexdigest(),
            ),
            sync_adapter=sync_adapter,
        )


@dataclass(slots=True, frozen=True)
class LoadedKnowledgeSource:
    definition: KnowledgeSourceDefinition
    documents: list[IngestDocument] = field(default_factory=list)
    filesystem_sources: list[IngestFilesystemSource] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def source_metadata(self) -> dict[str, Any]:
        version = self.definition.version
        return {
            **self.definition.metadata,
            **self.metadata,
            "loader_name": self.definition.loader_name,
            "display_name": self.definition.display_name,
            "source_type": self.definition.source_type,
            "version_revision": version.revision if version is not None else None,
            "version_observed_at": version.observed_at.isoformat() if version is not None else None,
        }


@dataclass(slots=True, frozen=True)
class KnowledgeIngestionResult:
    source_key: str
    loader_name: str
    source_type: str
    version_checksum: str | None
    ingested_documents: int
    ingested_chunks: int
    skipped_documents: int
    ingestion_runs: list[str] = field(default_factory=list)