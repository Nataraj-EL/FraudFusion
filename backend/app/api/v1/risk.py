from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, model_validator

from app.api.deps import get_optional_user
from app.schemas.auth import UserResponse
from app.schemas.signals import RiskAssessment
from app.schemas.transaction import Transaction
from app.services.audit_service import log_audit_event
from app.services.risk_engine import evaluate_risk_score

router = APIRouter()



class RiskScoreRequest(BaseModel):
    transaction: Transaction = Field(
        ...,
        description="Transaction object to evaluate",
    )
    custom_metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional ad-hoc metrics (e.g. distance_km, holding_minutes, domain_age_days)",
    )

    @model_validator(mode="before")
    @classmethod
    def extract_transaction_and_metrics(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "transaction" not in data and (
                "transaction_id" in data or "amount" in data or "account_id" in data
            ):
                custom = data.get("custom_metrics", {})
                tx_data = {k: v for k, v in data.items() if k != "custom_metrics"}
                return {"transaction": tx_data, "custom_metrics": custom}
        return data


@router.post(
    "/risk-score",
    response_model=RiskAssessment,
    status_code=status.HTTP_200_OK,
    summary="Compute consolidated risk score, risk band, recommended action, and explanation",
)
async def compute_risk_score(
    payload: RiskScoreRequest,
    current_user: UserResponse = Depends(get_optional_user),
) -> RiskAssessment:
    """
    Evaluates AF, FF, and PH signal engines, computes 0-100 subscores,
    aggregates consolidated risk score, determines risk band & recommended action,
    and returns concise deterministic explanation.
    """
    assessment = evaluate_risk_score(
        transaction=payload.transaction, custom_metrics=payload.custom_metrics
    )
    log_audit_event(
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="EVALUATE_RISK",
        resource_type="RISK_SCORE",
        transaction_id=assessment.transaction_id,
        status="SUCCESS",
        metadata={
            "consolidated_score": assessment.consolidated_score,
            "risk_band": assessment.risk_band,
            "recommended_action": assessment.recommended_action,
        },
    )
    return assessment

