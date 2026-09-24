from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    id: int | None = Field(default=None, description="Auto-incremented audit log ID")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="Audit event timestamp",
    )
    user_email: str = Field(..., description="User email executing action")
    user_role: str = Field(..., description="User RBAC role at execution time")
    action: str = Field(
        ..., description="Action code e.g. USER_LOGIN, EVALUATE_RISK, GENERATE_REPORT"
    )
    resource_type: str = Field(
        ..., description="Target domain e.g. AUTH, RISK_SCORE, REPORT, SYSTEM"
    )
    transaction_id: str | None = Field(
        default=None, description="Associated transaction ID if applicable"
    )
    status: str = Field(
        default="SUCCESS", description="Execution result: SUCCESS, FAILED, or UNAUTHORIZED"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional execution context parameters"
    )


class AuditLogQueryResponse(BaseModel):
    total_count: int = Field(..., ge=0, description="Total matching audit log entries count")
    logs: list[AuditLogEntry] = Field(
        default_factory=list, description="List of audit log records"
    )
