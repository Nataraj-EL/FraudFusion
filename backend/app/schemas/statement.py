from typing import Any

from pydantic import BaseModel, Field

from app.schemas.ingestion import IngestionResult


class ExtractedStatementTransaction(BaseModel):
    page_number: int = Field(default=1, description="Page/image index")
    raw_text: str = Field(..., description="Raw text line snippet")
    transaction_id: str | None = Field(default=None, description="Extracted reference ID")
    date: str | None = Field(default=None, description="Extracted date")
    account_id: str | None = Field(default=None, description="Extracted sender account ID")
    recipient_id: str | None = Field(default=None, description="Extracted recipient ID")
    amount: float | None = Field(default=None, description="Extracted amount")
    currency: str = Field(default="USD", description="Extracted currency ISO code")
    direction: str = Field(default="OUTBOUND", description="INBOUND | OUTBOUND")
    description: str | None = Field(default=None, description="Extracted description")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    confidence_level: str = Field(..., description="HIGH | MEDIUM | LOW | NEEDS_REVIEW")
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    validation_errors: list[str] = Field(default_factory=list)
    is_valid: bool = Field(default=True, description="Valid for normalization")


class StatementExtractionResult(BaseModel):
    batch_id: str = Field(..., description="Batch ID for statement upload")
    filename: str = Field(..., description="Uploaded statement filename")
    total_lines_scanned: int = Field(default=0, description="Total lines scanned")
    extracted_count: int = Field(..., ge=0, description="Extracted count")
    valid_count: int = Field(..., ge=0, description="Valid count")
    invalid_count: int = Field(..., ge=0, description="Rejected count")
    extracted_transactions: list[ExtractedStatementTransaction] = Field(default_factory=list)
    ocr_engine_used: str = Field(..., description="PyMuPDF_Text | Tesseract_OCR")
    ingestion_result: IngestionResult | None = Field(default=None)
