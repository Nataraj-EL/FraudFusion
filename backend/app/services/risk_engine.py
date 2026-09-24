from typing import Any

from app.core.config import load_risk_config, settings
from app.schemas.ingestion import CanonicalTransaction
from app.schemas.signals import RiskAssessment, SignalFactor
from app.schemas.transaction import Transaction
from app.services.signals import evaluate_all_signals

# Mapping of factor codes to natural-language driver descriptions for concise explanations
FACTOR_DRIVER_DESCRIPTIONS = {
    "AF1": "device fingerprint change",
    "AF2": "high geographic distance",
    "AF3": "transaction amount exceeding historical mean",
    "FF1": "unbalanced flow ratio",
    "FF2": "near-zero retained balance",
    "FF3": "short holding time",
    "PH1": "suspicious domain age",
    "PH2": "invalid or self-signed SSL certificate",
    "PH3": "blacklisted domain/IP",
}


def _determine_risk_band_and_action(score: float) -> tuple[str, str]:
    """
    Dynamically maps a consolidated score [0, 100] to a Risk Band and Recommended Action
    using the externalized risk_config.yaml configuration.
    """
    config = load_risk_config(settings.risk_config_path)
    rounded_score = int(round(score))

    for band_cfg in config.risk_bands:
        if band_cfg.min_score <= rounded_score <= band_cfg.max_score:
            return band_cfg.band, band_cfg.action

    # Fallback bounds safety
    if score <= 0:
        first = config.risk_bands[0]
        return first.band, first.action
    last = config.risk_bands[-1]
    return last.band, last.action


def _generate_explanation_summary(
    risk_band: str, score: float, triggered_factors: list[SignalFactor]
) -> str:
    """
    Generates a concise, deterministic overall explanation using top triggered signal factors.
    No LLMs or black-box models are used.
    Example: "High risk primarily driven by device fingerprint change and near-zero
    retained balance."

    """
    if not triggered_factors or score == 0.0:
        return (
            f"{risk_band} risk score of {score:.1f} with no anomalies or triggered risk factors."
        )

    # Sort triggered factors by weighted contribution descending
    sorted_factors = sorted(
        triggered_factors, key=lambda f: f.weighted_contribution, reverse=True
    )

    drivers: list[str] = []
    for f in sorted_factors:
        desc = FACTOR_DRIVER_DESCRIPTIONS.get(f.signal_id, f.name.lower())
        if desc not in drivers:
            drivers.append(desc)

    if len(drivers) == 1:
        return f"{risk_band} risk primarily driven by {drivers[0]}."

    top_two = f"{drivers[0]} and {drivers[1]}"
    return f"{risk_band} risk primarily driven by {top_two}."


def evaluate_risk_score(
    transaction: Transaction | CanonicalTransaction,
    custom_metrics: dict[str, Any] | None = None,
) -> RiskAssessment:
    """
    Consolidates Adaptive Friction (AF), Fund Flow (FF), and Phishing (PH) signals
    into a unified 0-100 risk score, risk band, recommended action, and concise explanation.
    """
    config = load_risk_config(settings.risk_config_path)

    # Evaluate all signal engines
    eval_result = evaluate_all_signals(transaction, custom_metrics)
    groups = eval_result.signal_groups

    af_group = groups.get("AF")
    ff_group = groups.get("FF")
    ph_group = groups.get("PH")

    # Compute Group Subscores [0, 100]
    af_subscore = round((af_group.raw_score if af_group else 0.0) * 100.0, 2)
    ff_subscore = round((ff_group.raw_score if ff_group else 0.0) * 100.0, 2)
    ph_subscore = round((ph_group.raw_score if ph_group else 0.0) * 100.0, 2)

    # Externalized group weights from risk_config.yaml
    af_weight = (
        config.signal_groups["adaptive_friction"].weight
        if "adaptive_friction" in config.signal_groups
        else 0.45
    )
    ff_weight = (
        config.signal_groups["fund_flow"].weight
        if "fund_flow" in config.signal_groups
        else 0.35
    )
    ph_weight = (
        config.signal_groups["phishing"].weight
        if "phishing" in config.signal_groups
        else 0.20
    )

    # Consolidated Score calculation and clipping
    raw_composite = (
        (af_subscore * af_weight) + (ff_subscore * ff_weight) + (ph_subscore * ph_weight)
    )
    consolidated_score = round(max(0.0, min(100.0, raw_composite)), 2)

    # Risk Band & Recommended Action lookup
    risk_band, recommended_action = _determine_risk_band_and_action(consolidated_score)

    # Collect Triggered Signals
    triggered_signals: list[SignalFactor] = []
    for grp in groups.values():
        for factor in grp.factors:
            if factor.triggered or factor.risk_factor > 0.0:
                triggered_signals.append(factor)

    # Generate Concise Explainability Text
    explanation = _generate_explanation_summary(risk_band, consolidated_score, triggered_signals)

    # Determine STR Eligibility (Critical band or action BLOCK_AND_REPORT or score >= 81)
    str_eligible = consolidated_score >= 81.0 or recommended_action == "BLOCK_AND_REPORT"

    tx_id = (
        transaction.transaction_id
        if hasattr(transaction, "transaction_id")
        else str(getattr(transaction, "reference_id", "UNKNOWN"))
    )

    return RiskAssessment(
        transaction_id=tx_id,
        af_subscore=af_subscore,
        ff_subscore=ff_subscore,
        ph_subscore=ph_subscore,
        consolidated_score=consolidated_score,
        risk_score=consolidated_score,
        risk_band=risk_band,
        recommended_action=recommended_action,
        explanation=explanation,
        explanation_summary=explanation,
        all_signal_results=groups,
        signal_groups=groups,
        triggered_signals=triggered_signals,
        str_report_eligible=str_eligible,
    )
