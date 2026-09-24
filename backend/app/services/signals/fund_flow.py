from typing import Any

from app.core.config import load_risk_config, settings
from app.schemas.ingestion import CanonicalTransaction
from app.schemas.signals import SignalFactor, SignalGroupResult
from app.schemas.transaction import Transaction


def evaluate_fund_flow(
    transaction: Transaction | CanonicalTransaction,
    custom_metrics: dict[str, Any] | None = None,
) -> SignalGroupResult:
    """
    Evaluates Fund Flow (FF) signals:
    - FF1: Balanced Flow Ratio (weight 0.45)
    - FF2: Near-zero Retained Balance (weight 0.30)
    - FF3: Short Holding Time (weight 0.25)
    """
    config = load_risk_config(settings.risk_config_path)
    ff_config = config.signal_groups.get("fund_flow")

    group_weight = ff_config.weight if ff_config else 0.35
    factors_cfg = ff_config.factors if ff_config else {}
    ff1_weight = factors_cfg["FF1"].weight if "FF1" in factors_cfg else 0.45
    ff2_weight = factors_cfg["FF2"].weight if "FF2" in factors_cfg else 0.30
    ff3_weight = factors_cfg["FF3"].weight if "FF3" in factors_cfg else 0.25

    # Extract metrics
    ff_metrics: dict[str, Any] = {}
    is_canonical = isinstance(transaction, CanonicalTransaction)
    if is_canonical and "ff_metrics" in transaction.source_metadata:
        ff_metrics.update(transaction.source_metadata["ff_metrics"])

    tx_meta = getattr(transaction, "metadata", None)
    if isinstance(tx_meta, dict):
        ff_metrics.update(tx_meta)

    if custom_metrics:
        ff_metrics.update(custom_metrics)

    # ---------------------------------------------------------
    # FF1: Balanced Flow Ratio
    # ---------------------------------------------------------
    in_deg = float(ff_metrics.get("in_degree", ff_metrics.get("in_degree_count", 0.0)))
    out_deg = float(ff_metrics.get("out_degree", ff_metrics.get("out_degree_count", 0.0)))

    in_deg = max(0.0, in_deg)
    out_deg = max(0.0, out_deg)

    larger_deg = max(in_deg, out_deg)
    smaller_deg = min(in_deg, out_deg)

    if larger_deg == 0.0:
        rf1 = 0.0
        exp1 = (
            "Balanced flow ratio: no incoming or outgoing transactions "
            "(in_degree=0, out_degree=0); risk factor=0.00."
        )
    else:
        ratio1 = smaller_deg / larger_deg
        rf1 = max(0.0, min(1.0, ratio1))
        if rf1 > 0.0:
            exp1 = (
                f"Balanced flow detected (pass-through structuring): in_degree={in_deg:.0f}, "
                f"out_degree={out_deg:.0f} (flow ratio={rf1:.2f}); risk factor={rf1:.2f}."
            )
        else:
            exp1 = (
                f"Unbalanced flow: in_degree={in_deg:.0f}, out_degree={out_deg:.0f}; "
                f"risk factor=0.00."
            )

    factor_ff1 = SignalFactor(
        signal_id="FF1",
        name="Balanced Flow Ratio",
        raw_value=rf1,
        raw_inputs={"in_degree": in_deg, "out_degree": out_deg},
        risk_factor=rf1,
        weight=ff1_weight,
        explanation=exp1,
    )

    # ---------------------------------------------------------
    # FF2: Near-zero Retained Balance
    # ---------------------------------------------------------
    if "total_sent" in ff_metrics and ff_metrics["total_sent"] is not None:
        total_sent = float(ff_metrics["total_sent"])
    elif "total_sent_amount" in ff_metrics and ff_metrics["total_sent_amount"] is not None:
        total_sent = float(ff_metrics["total_sent_amount"])
    else:
        total_sent = transaction.amount

    if "retained_balance" in ff_metrics and ff_metrics["retained_balance"] is not None:
        retained_bal = float(ff_metrics["retained_balance"])
    elif "remaining_balance" in ff_metrics and ff_metrics["remaining_balance"] is not None:
        retained_bal = float(ff_metrics["remaining_balance"])
    elif "balance_after" in ff_metrics and ff_metrics["balance_after"] is not None:
        retained_bal = float(ff_metrics["balance_after"])
    else:
        retained_bal = 0.0

    total_sent = max(0.0, total_sent)
    retained_bal = max(0.0, retained_bal)

    if total_sent == 0.0:
        rf2 = 0.0
        exp2 = "Retained balance evaluation skipped: total sent amount is zero; risk factor=0.00."
    else:
        retained_ratio = retained_bal / total_sent
        rf2 = max(0.0, min(1.0, 1.0 - retained_ratio))
        pct_retained = retained_ratio * 100.0
        curr_str = transaction.currency
        if rf2 > 0.0:
            exp2 = (
                f"Near-zero retained balance (rapid drain): sent={total_sent:.2f} {curr_str}, "
                f"retained={retained_bal:.2f} {curr_str} ({pct_retained:.2f}%); "
                f"risk factor={rf2:.2f}."
            )

        else:
            exp2 = (
                f"Sufficient retained balance: total_sent={total_sent:.2f} {curr_str}, "
                f"retained_balance={retained_bal:.2f} {curr_str}; risk factor=0.00."
            )


    factor_ff2 = SignalFactor(
        signal_id="FF2",
        name="Near-zero Retained Balance",
        raw_value=retained_bal,
        raw_inputs={"total_sent": total_sent, "retained_balance": retained_bal},
        risk_factor=rf2,
        weight=ff2_weight,
        explanation=exp2,
    )

    # ---------------------------------------------------------
    # FF3: Short Holding Time
    # ---------------------------------------------------------
    holding_mins = float(
        ff_metrics.get("holding_minutes")
        or ff_metrics.get("holding_time_minutes")
        or ff_metrics.get("dwell_time_minutes")
        or 60.0
    )
    holding_mins = max(0.0, holding_mins)
    rf3 = max(0.0, min(1.0, 1.0 - (holding_mins / 60.0)))

    if rf3 > 0.0:
        exp3 = (
            f"Short fund holding time: holding time is {holding_mins:.2f} minutes "
            f"(threshold 60.00 minutes); risk factor={rf3:.2f}."
        )
    else:
        exp3 = (
            f"Normal fund holding time: holding time is {holding_mins:.2f} minutes "
            f"(threshold 60.00 minutes); risk factor=0.00."
        )

    factor_ff3 = SignalFactor(
        signal_id="FF3",
        name="Short Holding Time",
        raw_value=holding_mins,
        raw_inputs={"holding_minutes": holding_mins, "threshold_minutes": 60.0},
        risk_factor=rf3,
        weight=ff3_weight,
        explanation=exp3,
    )

    # Aggregate Group Score
    factors = [factor_ff1, factor_ff2, factor_ff3]
    raw_group_score = sum(f.weighted_contribution for f in factors)

    return SignalGroupResult(
        group_code="FF",
        group_name="Fund Flow",
        group_weight=group_weight,
        raw_score=round(raw_group_score, 4),
        weighted_score=round(raw_group_score * group_weight, 4),
        factors=factors,
    )
