from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.schemas.ingestion import IngestionBatchSummary, IngestionResult, SourceType
from app.services.ingestion import ingestion_service

router = APIRouter()


@router.post(
    "/ingest/upload",
    response_model=IngestionResult,
    status_code=status.HTTP_201_CREATED,
    summary="Upload data file for ingestion and validation",
)
async def upload_ingest_file(
    file: Annotated[UploadFile, File(description="JSON or CSV source file to upload")],
    source_type: Annotated[
        SourceType | None,
        Form(
            description="Optional explicit source domain (ADAPTIVE_FRICTION, FUND_FLOW, PHISHING)"
        ),
    ] = None,
) -> IngestionResult:
    """
    Parses, validates, normalizes, and persists an uploaded batch file.
    Rejects malformed/invalid records cleanly with structured validation errors.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename",
        )


    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty"
        )

    result = ingestion_service.ingest_file(
        content=content, filename=file.filename, source_type=source_type
    )
    return result


@router.get(
    "/ingest/batches",
    response_model=list[IngestionBatchSummary],
    summary="List recent ingestion batch summaries",
)
async def list_ingestion_batches(limit: int = 50) -> list[IngestionBatchSummary]:
    """Retrieves audit summaries of recent ingestion batches."""
    return ingestion_service.list_batches(limit=limit)


@router.get(
    "/ingest/batches/{batch_id}",
    response_model=IngestionResult,
    summary="Get ingestion batch details",
)
async def get_ingestion_batch(batch_id: str) -> IngestionResult:
    """Retrieves full details, errors, and accepted records for a batch."""
    batch = ingestion_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion batch '{batch_id}' not found",
        )
    return batch
