from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.transaction import ChannelType, DeviceContext, PaymentMethod, TransactionStatus


class SourceType(str, Enum):
    ADAPTIVE_FRICTION = "ADAPTIVE_FRICTION"
    FUND_FLOW = "FUND_FLOW"
    PHISHING = "PHISHING"
    BANK_STATEMENT = "BANK_STATEMENT"



class ValidationErrorItem(BaseModel):
    record_index: int = Field(..., description="0-based row/item index in source file")
    reference_id: str | None = Field(
        default=None, description="Source reference or transaction ID if present"
    )
    field: str = Field(..., description="Field name that failed validation")
    reason: str = Field(..., description="Human-readable validation failure reason")
    source_type: SourceType = Field(..., description="Signal source type")


class CanonicalTransaction(BaseModel):
    transaction_id: str = Field(..., description="Canonical transaction identifier")
    source_type: SourceType = Field(..., description="Signal source domain")
    source_reference_id: str = Field(..., description="Original reference ID from source")
    account_id: str = Field(..., description="Sender or user account ID")
    recipient_id: str = Field(..., description="Beneficiary or destination entity ID")
    amount: float = Field(..., gt=0.0, description="Transaction amount")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    channel: ChannelType = Field(default=ChannelType.WEB)
    payment_method: PaymentMethod = Field(default=PaymentMethod.CREDIT_CARD)
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    device_context: DeviceContext = Field(default_factory=DeviceContext)
    source_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Preserved raw signal factors for AF/FF/PH evaluation",
    )


class IngestionBatchSummary(BaseModel):
    batch_id: str = Field(..., description="Unique batch identifier")
    source_type: SourceType = Field(..., description="Signal source type")
    filename: str = Field(..., description="Original uploaded filename")
    total_records: int = Field(..., ge=0)
    accepted_count: int = Field(..., ge=0)
    rejected_count: int = Field(..., ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class IngestionResult(BaseModel):
    batch: IngestionBatchSummary
    accepted_records: list[CanonicalTransaction] = Field(default_factory=list)
    validation_errors: list[ValidationErrorItem] = Field(default_factory=list)
