from typing import Any

from app.schemas.ingestion import CanonicalTransaction
from app.schemas.signals import SignalEvaluationResult
from app.schemas.transaction import Transaction
from app.services.signals.adaptive_friction import evaluate_adaptive_friction
from app.services.signals.fund_flow import evaluate_fund_flow
from app.services.signals.phishing import evaluate_phishing


def evaluate_all_signals(
    transaction: Transaction | CanonicalTransaction,
    custom_metrics: dict[str, Any] | None = None,
) -> SignalEvaluationResult:
    """
    Evaluates all three independent fraud-signal engines (Adaptive Friction, Fund Flow, Phishing).
    Returns structured evaluation result containing factor calculations, weights, and explanations.
    """
    af_result = evaluate_adaptive_friction(transaction, custom_metrics)
    ff_result = evaluate_fund_flow(transaction, custom_metrics)
    ph_result = evaluate_phishing(transaction, custom_metrics)

    source_type_val = (
        transaction.source_type.value
        if isinstance(transaction, CanonicalTransaction)
        else "TRANSACTION"
    )

    return SignalEvaluationResult(
        transaction_id=transaction.transaction_id,
        source_type=source_type_val,
        signal_groups={
            "AF": af_result,
            "FF": ff_result,
            "PH": ph_result,
        },
    )
