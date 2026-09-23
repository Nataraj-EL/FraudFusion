from typing import Any

from pydantic import BaseModel, Field, model_validator


class SignalFactor(BaseModel):
    name: str = Field(..., description="Name of the fraud signal factor")
    code: str = Field(..., description="Short factor code e.g. AF_SESSION_ANOMALY")
    raw_value: float = Field(..., description="Unclipped raw input metric")
    clipped_value: float = Field(
        default=0.0, description="Normalized score clipped to [0.0, 1.0]"
    )
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Weight within factor group")
    explanation: str = Field(..., description="Human-readable explanation of factor contribution")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def compute_clipped_value(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw = data.get("raw_value")
            has_clipped = "clipped_value" in data and data.get("clipped_value") is not None
            if raw is not None and not has_clipped:
                data["clipped_value"] = max(0.0, min(1.0, float(raw)))
            elif has_clipped:
                data["clipped_value"] = max(0.0, min(1.0, float(data["clipped_value"])))
        return data


class SignalGroupResult(BaseModel):
    group_code: str = Field(..., description="AF, FF, or PH")
    group_name: str = Field(..., description="Group name e.g. Adaptive Friction")
    group_weight: float = Field(
        ..., ge=0.0, le=1.0, description="Group weight in composite score"
    )
    raw_score: float = Field(
        ..., ge=0.0, le=1.0, description="Aggregated factor score for group [0, 1]"
    )
    weighted_score: float = Field(..., ge=0.0, description="Contribution to overall score")
    factors: list[SignalFactor] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    transaction_id: str
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Final composite risk score")
    risk_band: str = Field(..., description="Very Low, Low, Medium, High, or Critical")
    recommended_action: str = Field(
        ..., description="ALLOW, MONITOR, CHALLENGE, HOLD, BLOCK_AND_REPORT"
    )
    explanation_summary: str = Field(..., description="High-level explainability summary")
    signal_groups: dict[str, SignalGroupResult] = Field(default_factory=dict)
    str_report_eligible: bool = Field(
        default=False, description="Suspicious Transaction Report threshold"
    )

