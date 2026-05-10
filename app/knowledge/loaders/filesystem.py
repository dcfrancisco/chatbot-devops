from __future__ import annotations

from app.knowledge.loaders.base import BaseKnowledgeSourceLoader
from app.knowledge.sources.models import KnowledgeSourceDefinition, LoadedKnowledgeSource
from app.models.api import IngestFilesystemSource


class _FilesystemPatternLoader(BaseKnowledgeSourceLoader):
    glob_pattern = "**/*"
    format_name = "filesystem"

    async def load(self, definition: KnowledgeSourceDefinition) -> LoadedKnowledgeSource:
        return LoadedKnowledgeSource(
            definition=definition,
            filesystem_sources=[
                IngestFilesystemSource(
                    source_key=definition.source_key,
                    root_path=definition.uri,
                    glob_pattern=self.glob_pattern,
                    source_type=definition.source_type,
                    metadata={
                        **definition.metadata,
                        "loader_name": self.name,
                        "format": self.format_name,
                        "source_version": definition.version.checksum if definition.version is not None else None,
                    },
                )
            ],
            metadata={"ingestion_mode": "filesystem", "format": self.format_name},
        )


class MarkdownKnowledgeLoader(_FilesystemPatternLoader):
    name = "markdown-loader"
    description = "Loads markdown knowledge from filesystem-backed sources."
    source_kinds = ("markdown",)
    glob_pattern = "**/*.md"
    format_name = "markdown"


class YamlKnowledgeLoader(_FilesystemPatternLoader):
    name = "yaml-loader"
    description = "Loads yaml knowledge from filesystem-backed sources."
    source_kinds = ("yaml",)
    glob_pattern = "**/*.y*ml"
    format_name = "yaml"


class TextKnowledgeLoader(_FilesystemPatternLoader):
    name = "txt-loader"
    description = "Loads plain text knowledge from filesystem-backed sources."
    source_kinds = ("txt",)
    glob_pattern = "**/*.txt"
    format_name = "text"


class PdfKnowledgeLoader(_FilesystemPatternLoader):
    name = "pdf-loader"
    description = "Loads PDF knowledge from filesystem-backed sources."
    source_kinds = ("pdf",)
    glob_pattern = "**/*.pdf"
    format_name = "pdf"