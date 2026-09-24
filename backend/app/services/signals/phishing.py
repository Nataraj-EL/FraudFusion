from typing import Any

from app.core.config import load_risk_config, settings
from app.schemas.ingestion import CanonicalTransaction
from app.schemas.signals import SignalFactor, SignalGroupResult
from app.schemas.transaction import Transaction


def evaluate_phishing(
    transaction: Transaction | CanonicalTransaction,
    custom_metrics: dict[str, Any] | None = None,
) -> SignalGroupResult:
    """
    Evaluates Phishing (PH) signals:
    - PH1: Domain Age (weight 0.40)
    - PH2: Certificate Quality (weight 0.30)
    - PH3: Blacklist Hit (weight 0.30)
    """
    config = load_risk_config(settings.risk_config_path)
    ph_config = config.signal_groups.get("phishing")

    group_weight = ph_config.weight if ph_config else 0.20
    factors_cfg = ph_config.factors if ph_config else {}
    ph1_weight = factors_cfg["PH1"].weight if "PH1" in factors_cfg else 0.40
    ph2_weight = factors_cfg["PH2"].weight if "PH2" in factors_cfg else 0.30
    ph3_weight = factors_cfg["PH3"].weight if "PH3" in factors_cfg else 0.30

    # Extract metrics
    ph_metrics: dict[str, Any] = {}
    is_canonical = isinstance(transaction, CanonicalTransaction)
    if is_canonical and "ph_metrics" in transaction.source_metadata:
        ph_metrics.update(transaction.source_metadata["ph_metrics"])

    tx_meta = getattr(transaction, "metadata", None)
    if isinstance(tx_meta, dict):
        ph_metrics.update(tx_meta)

    if custom_metrics:
        ph_metrics.update(custom_metrics)

    # ---------------------------------------------------------
    # PH1: Domain Age
    # ---------------------------------------------------------
    dad_val = None
    for k in ("domain_age_days", "age_days", "domain_age"):
        if k in ph_metrics and ph_metrics[k] is not None:
            dad_val = ph_metrics[k]
            break
    domain_age_days = float(dad_val) if dad_val is not None else 180.0

    domain_age_days = max(0.0, domain_age_days)
    rf1 = max(0.0, min(1.0, 1.0 - (domain_age_days / 180.0)))

    if rf1 > 0.0:
        exp1 = (
            f"Short domain age: domain age is {domain_age_days:.2f} days "
            f"(threshold 180.00 days); risk factor={rf1:.2f}."
        )
    else:
        exp1 = (
            f"Established domain age: domain age is {domain_age_days:.2f} days "
            f"(threshold 180.00 days); risk factor=0.00."
        )

    factor_ph1 = SignalFactor(
        signal_id="PH1",
        name="Domain Age",
        raw_value=domain_age_days,
        raw_inputs={"domain_age_days": domain_age_days, "threshold_days": 180.0},
        risk_factor=rf1,
        weight=ph1_weight,
        explanation=exp1,
    )

    # ---------------------------------------------------------
    # PH2: Certificate Quality
    # ---------------------------------------------------------
    self_signed = bool(
        ph_metrics.get("self_signed")
        or ph_metrics.get("selfSigned")
        or ph_metrics.get("certificate_self_signed")
        or False
    )

    validity_days = ph_metrics.get("validity_days") or ph_metrics.get("certificate_validity_days")
    if validity_days is not None:
        validity_days = float(validity_days)
    else:
        validity_days = 365.0  # Default to valid standard cert

    cert_substandard = self_signed or (validity_days < 30.0)
    rf2 = 1.0 if cert_substandard else 0.0

    if self_signed:
        exp2 = "Substandard SSL certificate: certificate is self-signed; risk factor=1.00."
    elif validity_days < 30.0:
        exp2 = (
            f"Substandard SSL certificate: certificate validity is {validity_days:.0f} days "
            f"(threshold < 30 days); risk factor=1.00."
        )
    else:
        exp2 = (
            f"Standard SSL certificate: trusted authority, {validity_days:.0f} days validity; "
            f"risk factor=0.00."
        )

    factor_ph2 = SignalFactor(
        signal_id="PH2",
        name="Certificate Quality",
        raw_value=rf2,
        raw_inputs={"self_signed": self_signed, "validity_days": validity_days},
        risk_factor=rf2,
        weight=ph2_weight,
        explanation=exp2,
    )

    # ---------------------------------------------------------
    # PH3: Blacklist Hit
    # ---------------------------------------------------------
    local_listing = str(
        ph_metrics.get("local_listing")
        or ph_metrics.get("localListing")
        or ph_metrics.get("listing_status")
        or "clean"
    ).lower()

    is_blacklisted = local_listing == "blacklist"
    rf3 = 1.0 if is_blacklisted else 0.0

    if is_blacklisted:
        exp3 = (
            "Phishing blacklist match: entity domain listed on local blacklist; "
            "risk factor=1.00."
        )
    else:
        exp3 = (
            f"No blacklist match: entity domain listing status='{local_listing}'; "
            f"risk factor=0.00."
        )


    factor_ph3 = SignalFactor(
        signal_id="PH3",
        name="Blacklist Hit",
        raw_value=rf3,
        raw_inputs={"local_listing": local_listing, "blacklisted": is_blacklisted},
        risk_factor=rf3,
        weight=ph3_weight,
        explanation=exp3,
    )

    # Aggregate Group Score
    factors = [factor_ph1, factor_ph2, factor_ph3]
    raw_group_score = sum(f.weighted_contribution for f in factors)

    return SignalGroupResult(
        group_code="PH",
        group_name="Phishing",
        group_weight=group_weight,
        raw_score=round(raw_group_score, 4),
        weighted_score=round(raw_group_score * group_weight, 4),
        factors=factors,
    )
