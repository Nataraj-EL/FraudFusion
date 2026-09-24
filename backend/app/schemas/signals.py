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
    af_subscore: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Adaptive Friction subscore (0-100)"
    )
    ff_subscore: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Fund Flow subscore (0-100)"
    )
    ph_subscore: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Phishing subscore (0-100)"
    )


    consolidated_score: float = Field(
        ..., ge=0.0, le=100.0, description="Final composite risk score (0-100)"
    )
    risk_score: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Alias for consolidated_score"
    )
    risk_band: str = Field(..., description="Very Low, Low, Medium, High, or Critical")
    recommended_action: str = Field(
        ..., description="ALLOW, MONITOR, CHALLENGE, HOLD, BLOCK_AND_REPORT"
    )
    explanation: str = Field(..., description="Concise overall explainability text")
    explanation_summary: str = Field(default="", description="Alias for explanation")
    all_signal_results: dict[str, SignalGroupResult] = Field(
        default_factory=dict, description="All signal evaluation groups (AF, FF, PH)"
    )
    signal_groups: dict[str, SignalGroupResult] = Field(
        default_factory=dict, description="Alias for all_signal_results"
    )
    triggered_signals: list[SignalFactor] = Field(
        default_factory=list, description="List of factors with risk_factor > 0"
    )
    str_report_eligible: bool = Field(
        default=False, description="Suspicious Transaction Report threshold"
    )

    @model_validator(mode="before")
    @classmethod
    def sync_risk_assessment_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Sync consolidated_score and risk_score
            cs = data.get("consolidated_score")
            rs = data.get("risk_score")
            val = cs if cs is not None else rs
            if val is not None:
                val = round(max(0.0, min(100.0, float(val))), 2)
                data["consolidated_score"] = val
                data["risk_score"] = val

            # Sync explanation and explanation_summary
            exp = data.get("explanation") or data.get("explanation_summary") or ""
            data["explanation"] = exp
            data["explanation_summary"] = exp

            # Sync all_signal_results and signal_groups
            asr = data.get("all_signal_results") or data.get("signal_groups") or {}
            data["all_signal_results"] = asr
            data["signal_groups"] = asr
        return data

