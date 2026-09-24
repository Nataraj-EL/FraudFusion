from typing import Any

from app.core.config import load_risk_config, settings
from app.schemas.ingestion import CanonicalTransaction
from app.schemas.signals import SignalFactor, SignalGroupResult
from app.schemas.transaction import Transaction


def evaluate_adaptive_friction(
    transaction: Transaction | CanonicalTransaction,
    custom_metrics: dict[str, Any] | None = None,
) -> SignalGroupResult:
    """
    Evaluates Adaptive Friction (AF) signals:
    - AF1: Device Fingerprint Delta (weight 0.50)
    - AF2: Geo Distance (weight 0.30)
    - AF3: Amount vs Historical Mean (weight 0.20)
    """
    config = load_risk_config(settings.risk_config_path)
    af_config = config.signal_groups.get("adaptive_friction")

    group_weight = af_config.weight if af_config else 0.45
    factors_cfg = af_config.factors if af_config else {}
    af1_weight = factors_cfg["AF1"].weight if "AF1" in factors_cfg else 0.50
    af2_weight = factors_cfg["AF2"].weight if "AF2" in factors_cfg else 0.30
    af3_weight = factors_cfg["AF3"].weight if "AF3" in factors_cfg else 0.20


    # Extract metrics from source_metadata or metadata or custom_metrics
    af_metrics: dict[str, Any] = {}
    is_canonical = isinstance(transaction, CanonicalTransaction)
    if is_canonical and "af_metrics" in transaction.source_metadata:
        af_metrics.update(transaction.source_metadata["af_metrics"])

    tx_meta = getattr(transaction, "metadata", None)
    if isinstance(tx_meta, dict):
        af_metrics.update(tx_meta)

    if custom_metrics:
        af_metrics.update(custom_metrics)

    # ---------------------------------------------------------
    # AF1: Device Fingerprint Delta
    # ---------------------------------------------------------
    stored_fp = af_metrics.get("stored_device") or af_metrics.get("stored_fingerprint") or {}
    if isinstance(stored_fp, str):
        stored_fp = {"user_agent": stored_fp}

    current_dev = transaction.device_context
    curr_os = af_metrics.get("os") or current_dev.user_agent or "Unknown OS"
    curr_browser = af_metrics.get("browser") or current_dev.user_agent or "Unknown Browser"
    curr_ip = current_dev.ip_address or af_metrics.get("ip_address") or "0.0.0.0"

    stored_browser = stored_fp.get("browser") or stored_fp.get("user_agent")
    stored_ip = stored_fp.get("ip_address")
    stored_os = stored_fp.get("os")

    fingerprint_changed = False
    mismatch_details: list[str] = []

    if stored_browser and stored_browser != curr_browser:
        fingerprint_changed = True
        mismatch_details.append(f"browser='{curr_browser}' differs from stored '{stored_browser}'")
    if stored_ip and stored_ip != curr_ip:
        fingerprint_changed = True
        mismatch_details.append(f"IP='{curr_ip}' differs from stored '{stored_ip}'")
    if stored_os and stored_os != curr_os:
        fingerprint_changed = True
        mismatch_details.append(f"OS='{curr_os}' differs from stored '{stored_os}'")

    # Explicit override flag if provided in synthetic data
    if "device_fingerprint_changed" in af_metrics:
        fingerprint_changed = bool(af_metrics["device_fingerprint_changed"])
        if fingerprint_changed and not mismatch_details:
            mismatch_details.append("device hardware fingerprint delta detected")

    rf1 = 1.0 if fingerprint_changed else 0.0
    if rf1 > 0.0:
        details_str = "; ".join(mismatch_details) if mismatch_details else "fingerprint delta"
        exp1 = f"Device fingerprint changed: {details_str}; risk factor={rf1:.2f}."
    else:
        exp1 = (
            f"Device fingerprint match: browser='{curr_browser}', IP='{curr_ip}'; "
            f"risk factor=0.00."
        )

    factor_af1 = SignalFactor(
        signal_id="AF1",
        name="Device Fingerprint Delta",
        raw_value=rf1,
        raw_inputs={
            "current_browser": curr_browser,
            "stored_browser": stored_browser,
            "current_ip": curr_ip,
            "stored_ip": stored_ip,
            "fingerprint_changed": fingerprint_changed,
        },
        risk_factor=rf1,
        weight=af1_weight,
        explanation=exp1,
    )

    # ---------------------------------------------------------
    # AF2: Geo Distance
    # ---------------------------------------------------------
    dist_km = float(af_metrics.get("distance_km") or af_metrics.get("geo_distance_km") or 0.0)
    dist_km = max(0.0, dist_km)
    rf2 = max(0.0, min(1.0, dist_km / 1500.0))

    if rf2 > 0.0:
        exp2 = (
            f"Geographic distance anomaly: login distance is {dist_km:.2f} km "
            f"(threshold 1500.00 km); risk factor={rf2:.2f}."
        )
    else:
        exp2 = f"Geographic distance normal: login distance is {dist_km:.2f} km; risk factor=0.00."

    factor_af2 = SignalFactor(
        signal_id="AF2",
        name="Geo Distance",
        raw_value=dist_km,
        raw_inputs={"distance_km": dist_km, "threshold_km": 1500.0},
        risk_factor=rf2,
        weight=af2_weight,
        explanation=exp2,
    )

    # ---------------------------------------------------------
    # AF3: Amount vs Historical Mean
    # ---------------------------------------------------------
    mean_amt = float(
        af_metrics.get("historical_mean_amount") or af_metrics.get("mean_amount") or 0.0
    )
    amt = transaction.amount

    if mean_amt <= 0.0:
        rf3 = 0.0
        exp3 = (
            f"Amount evaluation skipped: historical mean amount is unavailable "
            f"or zero ({mean_amt:.2f} USD); risk factor=0.00."
        )


    else:
        ratio = (amt - mean_amt) / mean_amt
        rf3 = max(0.0, min(1.0, ratio))
        ratio_pct = ratio * 100.0
        curr_str = transaction.currency
        if rf3 > 0.0:
            exp3 = (
                f"Transaction amount exceeds historical mean: amount={amt:.2f} {curr_str} "
                f"vs mean={mean_amt:.2f} {curr_str} (+{ratio_pct:.2f}%); risk factor={rf3:.2f}."
            )
        else:
            exp3 = (
                f"Transaction amount within historical mean: amount={amt:.2f} {curr_str} "
                f"vs mean={mean_amt:.2f} {curr_str}; risk factor=0.00."
            )


    factor_af3 = SignalFactor(
        signal_id="AF3",
        name="Amount vs Historical Mean",
        raw_value=amt,
        raw_inputs={"amount": amt, "historical_mean_amount": mean_amt},
        risk_factor=rf3,
        weight=af3_weight,
        explanation=exp3,
    )

    # Aggregate Group Score
    factors = [factor_af1, factor_af2, factor_af3]
    raw_group_score = sum(f.weighted_contribution for f in factors)

    return SignalGroupResult(
        group_code="AF",
        group_name="Adaptive Friction",
        group_weight=group_weight,
        raw_score=round(raw_group_score, 4),
        weighted_score=round(raw_group_score * group_weight, 4),
        factors=factors,
    )
