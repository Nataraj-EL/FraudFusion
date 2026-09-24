from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import require_roles
from app.schemas.auth import UserResponse
from app.schemas.ingestion import IngestionBatchSummary, IngestionResult, SourceType
from app.schemas.statement import StatementExtractionResult
from app.services.audit_service import log_audit_event
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


@router.post(
    "/ingest/statement",
    response_model=StatementExtractionResult,
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF or Image bank statement for OCR extraction & pipeline validation",
)
async def upload_bank_statement(
    file: Annotated[UploadFile, File(description="PDF or Image bank statement file")],
    current_user: UserResponse = Depends(require_roles(["Analyst", "Admin"])),
) -> StatementExtractionResult:
    """
    Extracts transaction records from PDF/Image statements using OCR/PyMuPDF,
    validates and normalizes them through canonical pipeline, and persists to SQLite.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded statement file must have a valid filename",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded statement file is empty"
        )

    result = ingestion_service.ingest_statement(content=content, filename=file.filename)

    log_audit_event(
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="INGEST_STATEMENT",
        resource_type="STATEMENT_OCR",
        status="SUCCESS",
        metadata={
            "filename": file.filename,
            "extracted_count": result.extracted_count,
            "valid_count": result.valid_count,
            "ocr_engine_used": result.ocr_engine_used,
        },
    )
    return result

