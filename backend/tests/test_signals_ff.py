from app.schemas.transaction import Transaction
from app.services.signals.fund_flow import evaluate_fund_flow


def test_ff1_balanced_flow_ratio() -> None:
    tx = Transaction(
        transaction_id="TX-FF1-1", account_id="ACC-1", recipient_id="ACC-2", amount=500.0
    )

    # 1. Balanced flow: in 10, out 10 -> ratio 1.00
    res_bal = evaluate_fund_flow(tx, custom_metrics={"in_degree": 10, "out_degree": 10})
    f_bal = res_bal.factors[0]
    assert f_bal.signal_id == "FF1"
    assert f_bal.risk_factor == 1.00
    assert f_bal.triggered is True
    assert "Balanced flow detected" in f_bal.explanation

    # 2. Unbalanced flow: in 2, out 10 -> ratio 2/10 = 0.20
    res_unbal = evaluate_fund_flow(tx, custom_metrics={"in_degree": 2, "out_degree": 10})
    f_unbal = res_unbal.factors[0]
    assert f_unbal.risk_factor == 0.20

    # 3. Zero flow edge case: larger = 0 -> 0.00
    res_zero = evaluate_fund_flow(tx, custom_metrics={"in_degree": 0, "out_degree": 0})
    f_zero = res_zero.factors[0]
    assert f_zero.risk_factor == 0.00
    assert f_zero.triggered is False


def test_ff2_near_zero_retained_balance() -> None:
    tx = Transaction(
        transaction_id="TX-FF2-1", account_id="ACC-1", recipient_id="ACC-2", amount=10000.0
    )

    # 1. Rapid drain: sent 10000, retained 100 -> ratio 100/10000 = 0.01 -> 1 - 0.01 = 0.99
    res_drain = evaluate_fund_flow(
        tx, custom_metrics={"total_sent": 10000.0, "retained_balance": 100.0}
    )
    f_drain = res_drain.factors[1]
    assert f_drain.signal_id == "FF2"
    assert f_drain.risk_factor == 0.99
    assert f_drain.triggered is True
    assert "Near-zero retained balance" in f_drain.explanation

    # 2. Retained balance >= total sent -> 1 - (5000/1000) = negative -> clipped to 0.00
    res_safe = evaluate_fund_flow(
        tx, custom_metrics={"total_sent": 1000.0, "retained_balance": 5000.0}
    )
    f_safe = res_safe.factors[1]
    assert f_safe.risk_factor == 0.00
    assert f_safe.triggered is False

    # 3. Total sent = 0 edge case
    res_zero_sent = evaluate_fund_flow(
        tx, custom_metrics={"total_sent": 0.0, "retained_balance": 0.0}
    )
    f_zero_sent = res_zero_sent.factors[1]
    assert f_zero_sent.risk_factor == 0.00


def test_ff3_short_holding_time() -> None:
    tx = Transaction(
        transaction_id="TX-FF3-1", account_id="ACC-1", recipient_id="ACC-2", amount=500.0
    )

    # 1. Holding time 6 mins -> 1 - (6/60) = 0.90
    res_6m = evaluate_fund_flow(tx, custom_metrics={"holding_minutes": 6.0})
    f_6m = res_6m.factors[2]
    assert f_6m.signal_id == "FF3"
    assert f_6m.risk_factor == 0.90
    assert f_6m.triggered is True
    assert "Short fund holding time" in f_6m.explanation

    # 2. Holding time 120 mins -> 1 - (120/60) = -1.0 -> clipped to 0.00
    res_120m = evaluate_fund_flow(tx, custom_metrics={"holding_minutes": 120.0})
    f_120m = res_120m.factors[2]
    assert f_120m.risk_factor == 0.00
    assert f_120m.triggered is False
