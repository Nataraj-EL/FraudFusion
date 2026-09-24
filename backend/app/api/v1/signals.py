from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.schemas.signals import SignalEvaluationResult
from app.schemas.transaction import Transaction
from app.services.signals import evaluate_all_signals

router = APIRouter()


class SignalEvaluationRequest(BaseModel):
    transaction: Transaction = Field(
        ..., description="Transaction or canonical record object to evaluate"
    )
    custom_metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional ad-hoc metrics (e.g. distance_km, holding_minutes, domain_age_days)",
    )


@router.post(
    "/signals/evaluate",
    response_model=SignalEvaluationResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate independent fraud-signal engines (AF, FF, PH) for a transaction",
)
async def evaluate_transaction_signals(
    payload: SignalEvaluationRequest,
) -> SignalEvaluationResult:
    """
    Evaluates Adaptive Friction (AF1-AF3), Fund Flow (FF1-FF3), and Phishing (PH1-PH3)
    signal engines for the provided transaction, returning risk factors, weights, and explanations.
    """
    return evaluate_all_signals(
        transaction=payload.transaction, custom_metrics=payload.custom_metrics
    )
