from typing import Any

from pydantic import BaseModel, Field, model_validator


class SignalFactor(BaseModel):
    signal_id: str = Field(..., description="Unique signal code e.g. AF1, FF2, PH3")
    name: str = Field(..., description="Human-readable factor name")
    code: str = Field(default="", description="Legacy or short factor code")
    raw_value: float = Field(default=0.0, description="Primary raw metric value")
    raw_inputs: dict[str, Any] = Field(
        default_factory=dict, description="Raw input fields and values used for calculation"
    )
    risk_factor: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Normalized risk factor score clipped to [0, 1]"
    )
    clipped_value: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Alias for risk_factor"
    )
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Factor weight within group")
    weighted_contribution: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Risk factor * weight"
    )
    triggered: bool = Field(default=False, description="Whether factor risk_factor > 0")
    explanation: str = Field(..., description="Plain-language explanation detailing fields & math")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def sync_factor_values(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Sync code and signal_id
            if "signal_id" in data and not data.get("code"):
                data["code"] = data["signal_id"]
            elif "code" in data and not data.get("signal_id"):
                data["signal_id"] = data["code"]

            # Resolve risk_factor vs clipped_value
            rf = data.get("risk_factor")
            cv = data.get("clipped_value")
            val = rf if rf is not None else (cv if cv is not None else data.get("raw_value", 0.0))
            clipped = round(max(0.0, min(1.0, float(val))), 4)
            data["risk_factor"] = clipped
            data["clipped_value"] = clipped


            # Sync triggered
            data["triggered"] = clipped > 0.0

            # Sync weighted contribution
            w = float(data.get("weight", 1.0))
            data["weighted_contribution"] = round(clipped * w, 4)
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


class SignalEvaluationResult(BaseModel):
    transaction_id: str
    source_type: str = Field(default="UNKNOWN", description="Signal source domain")
    signal_groups: dict[str, SignalGroupResult] = Field(
        default_factory=dict, description="Evaluation results keyed by group code (AF, FF, PH)"
    )


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
