from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ChannelType(str, Enum):
    WEB = "WEB"
    MOBILE_APP = "MOBILE_APP"
    API = "API"
    ATM = "ATM"
    POS = "POS"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    FLAGGED = "FLAGGED"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    WIRE_TRANSFER = "WIRE_TRANSFER"
    ACH = "ACH"
    CRYPTO = "CRYPTO"
    P2P = "P2P"


class DeviceContext(BaseModel):
    device_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    is_vpn: bool = False
    is_tor: bool = False
    location_country: str | None = None


class Transaction(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction identifier")
    account_id: str = Field(..., description="Sender account or user ID")
    recipient_id: str = Field(..., description="Beneficiary account or entity ID")
    amount: float = Field(..., gt=0.0, description="Transaction amount in base currency")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    channel: ChannelType = ChannelType.WEB
    payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD
    status: TransactionStatus = TransactionStatus.PENDING
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    device_context: DeviceContext = Field(default_factory=DeviceContext)
    metadata: dict[str, Any] = Field(default_factory=dict)

