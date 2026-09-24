from app.schemas.transaction import DeviceContext, Transaction
from app.services.signals.adaptive_friction import evaluate_adaptive_friction


def test_af1_device_fingerprint_delta() -> None:
    # Triggered case
    tx_triggered = Transaction(
        transaction_id="TX-AF1-1",
        account_id="ACC-1",
        recipient_id="ACC-2",
        amount=100.0,
        device_context=DeviceContext(user_agent="Chrome 120", ip_address="192.168.1.1"),
    )
    res_trig = evaluate_adaptive_friction(
        tx_triggered,
        custom_metrics={"stored_device": {"browser": "Firefox 115", "ip_address": "192.168.1.1"}},
    )

    factor_af1 = res_trig.factors[0]
    assert factor_af1.signal_id == "AF1"
    assert factor_af1.risk_factor == 1.0
    assert factor_af1.triggered is True
    assert "Device fingerprint changed" in factor_af1.explanation
    assert "Chrome 120" in factor_af1.explanation

    # Non-triggered case
    res_match = evaluate_adaptive_friction(
        tx_triggered,
        custom_metrics={"stored_device": {"browser": "Chrome 120", "ip_address": "192.168.1.1"}},
    )
    factor_match = res_match.factors[0]
    assert factor_match.risk_factor == 0.0
    assert factor_match.triggered is False
    assert "Device fingerprint match" in factor_match.explanation


def test_af2_geo_distance_math_and_clipping() -> None:
    tx = Transaction(
        transaction_id="TX-AF2-1", account_id="ACC-1", recipient_id="ACC-2", amount=100.0
    )

    # 1. Normal value: 750km / 1500km = 0.50
    res_750 = evaluate_adaptive_friction(tx, custom_metrics={"distance_km": 750.0})
    f_750 = res_750.factors[1]
    assert f_750.signal_id == "AF2"
    assert f_750.risk_factor == 0.50
    assert f_750.triggered is True
    assert "750.00 km" in f_750.explanation

    # 2. Clipping case: 3000km / 1500km = 2.0 -> clipped to 1.00
    res_3000 = evaluate_adaptive_friction(tx, custom_metrics={"distance_km": 3000.0})
    f_3000 = res_3000.factors[1]
    assert f_3000.risk_factor == 1.00

    # 3. Boundary zero
    res_zero = evaluate_adaptive_friction(tx, custom_metrics={"distance_km": 0.0})
    f_zero = res_zero.factors[1]
    assert f_zero.risk_factor == 0.00
    assert f_zero.triggered is False


def test_af3_amount_vs_historical_mean() -> None:
    # 1. Amount 150 vs Mean 100 -> diff 50/100 = 0.50
    tx150 = Transaction(
        transaction_id="TX-AF3-1", account_id="ACC-1", recipient_id="ACC-2", amount=150.0
    )
    res_150 = evaluate_adaptive_friction(tx150, custom_metrics={"historical_mean_amount": 100.0})
    f_150 = res_150.factors[2]
    assert f_150.signal_id == "AF3"
    assert f_150.risk_factor == 0.50
    assert f_150.triggered is True
    assert "exceeds historical mean" in f_150.explanation

    # 2. Amount 80 vs Mean 100 -> negative diff -> clipped to 0.00
    tx80 = Transaction(
        transaction_id="TX-AF3-2", account_id="ACC-1", recipient_id="ACC-2", amount=80.0
    )
    res_80 = evaluate_adaptive_friction(tx80, custom_metrics={"historical_mean_amount": 100.0})
    f_80 = res_80.factors[2]
    assert f_80.risk_factor == 0.00
    assert f_80.triggered is False

    # 3. Zero historical mean edge case
    res_zero_mean = evaluate_adaptive_friction(
        tx150, custom_metrics={"historical_mean_amount": 0.0}
    )
    f_zero_mean = res_zero_mean.factors[2]
    assert f_zero_mean.risk_factor == 0.00
    assert "unavailable or zero" in f_zero_mean.explanation
