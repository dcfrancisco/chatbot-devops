import argparse
import asyncio
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import AsyncSessionLocal
from app.models.api import IngestFilesystemSource
from app.rag.ingestion import IngestionService
from app.services.llm import OpenAICompatibleProvider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest local documents into the RAG knowledge base")
    parser.add_argument("root_path", help="Root directory containing documents to ingest")
    parser.add_argument("--source-key", required=True, help="Stable key for the source")
    parser.add_argument("--glob", dest="glob_pattern", default="**/*", help="Glob pattern to match files")
    parser.add_argument("--source-type", default="filesystem", help="Source type label")
    parser.add_argument("--full-refresh", action="store_true", help="Disable incremental deduplication checks")
    parser.add_argument("--metadata", default="{}", help="JSON metadata to attach to the source")
    return parser


async def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)
    logger = get_logger(__name__)
    llm_provider = OpenAICompatibleProvider(settings)
    ingestion_service = IngestionService(settings, llm_provider)

    metadata = json.loads(args.metadata)
    source = IngestFilesystemSource(
        source_key=args.source_key,
        root_path=str(Path(args.root_path).expanduser().resolve()),
        glob_pattern=args.glob_pattern,
        source_type=args.source_type,
        metadata=metadata,
    )

    async with AsyncSessionLocal() as session:
        result = await ingestion_service.ingest_filesystem_sources(
            session,
            [source],
            incremental=not args.full_refresh,
        )

    logger.info(
        "ingestion_complete",
        extra={
            "source_key": args.source_key,
            "ingested_documents": result.ingested_documents,
            "ingested_chunks": result.ingested_chunks,
            "skipped_documents": result.skipped_documents,
            "ingestion_runs": result.ingestion_runs,
        },
    )


if __name__ == "__main__":
    asyncio.run(main())