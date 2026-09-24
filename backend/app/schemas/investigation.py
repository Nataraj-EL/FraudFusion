from typing import Any

from pydantic import BaseModel, Field

from app.schemas.ingestion import CanonicalTransaction
from app.schemas.report import RiskReport


class TransactionSummaryItem(BaseModel):
    transaction_id: str
    source_type: str
    account_id: str
    recipient_id: str
    amount: float
    currency: str
    channel: str
    payment_method: str
    timestamp: str
    consolidated_score: float | None = None
    risk_band: str = "Unassessed"
    recommended_action: str | None = None
    str_status: str = "NOT_REQUIRED"
    report_status: str = "UNASSESSED"


TransactionListItem = TransactionSummaryItem



class DashboardSummary(BaseModel):
    total_transactions: int = Field(..., description="Total persisted normalized transactions")
    risk_band_counts: dict[str, int] = Field(
        ..., description="Count of transactions grouped by risk band"
    )
    recent_high_risk: list[TransactionSummaryItem] = Field(
        default_factory=list, description="Recent transactions flagged with High/Critical risk"
    )
    pending_investigations: list[TransactionSummaryItem] = Field(
        default_factory=list, description="High/Critical transactions requiring analyst review"
    )
    recent_audit_logs: list[dict[str, Any]] = Field(
        default_factory=list, description="Recent audit log activity"
    )


class TransactionListResponse(BaseModel):
    total: int
    items: list[TransactionSummaryItem]


class FundFlowNode(BaseModel):
    id: str
    label: str
    role: str = Field(..., description="sender | recipient | intermediate | counterparty")
    risk_level: str = Field("normal", description="normal | suspicious | critical")


class FundFlowEdge(BaseModel):
    source: str
    target: str
    amount: float
    currency: str
    holding_minutes: float | None = None
    flow_type: str = "TRANSFER"
    is_suspicious: bool = False


class FundFlowVisualizationData(BaseModel):
    transaction_id: str
    nodes: list[FundFlowNode]
    edges: list[FundFlowEdge]
    metrics: dict[str, Any]
    explanation: str


class InvestigationDetail(BaseModel):
    transaction: CanonicalTransaction
    risk_report: RiskReport | None = None
    fund_flow: FundFlowVisualizationData | None = None
    audit_history: list[dict[str, Any]] = Field(default_factory=list)
