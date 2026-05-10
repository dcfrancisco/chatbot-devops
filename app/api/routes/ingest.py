from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_container, get_session
from app.core.container import ServiceContainer
from app.models.api import IngestRequest, IngestResponse

router = APIRouter(tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest(
    request: IngestRequest,
    container: ServiceContainer = Depends(get_container),
    session: AsyncSession = Depends(get_session),
) -> IngestResponse:
    documents_result = IngestResponse(ingested_documents=0, ingested_chunks=0, skipped_documents=0, ingestion_runs=[])
    filesystem_result = IngestResponse(ingested_documents=0, ingested_chunks=0, skipped_documents=0, ingestion_runs=[])

    if request.documents:
        documents_result = await container.ingestion_service.ingest_documents(
            session,
            request.documents,
            incremental=request.incremental,
        )
    if request.filesystem_sources:
        filesystem_result = await container.ingestion_service.ingest_filesystem_sources(
            session,
            request.filesystem_sources,
            incremental=request.incremental,
        )

    return IngestResponse(
        ingested_documents=documents_result.ingested_documents + filesystem_result.ingested_documents,
        ingested_chunks=documents_result.ingested_chunks + filesystem_result.ingested_chunks,
        skipped_documents=documents_result.skipped_documents + filesystem_result.skipped_documents,
        ingestion_runs=[*documents_result.ingestion_runs, *filesystem_result.ingestion_runs],
    )
