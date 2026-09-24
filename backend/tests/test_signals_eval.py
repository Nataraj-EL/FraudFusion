from fastapi.testclient import TestClient

from app.schemas.ingestion import CanonicalTransaction, SourceType
from app.schemas.transaction import ChannelType, DeviceContext, PaymentMethod, TransactionStatus
from app.services.signals import evaluate_all_signals


def test_evaluate_all_signals_integration() -> None:
    canonical_tx = CanonicalTransaction(
        transaction_id="TX-INTEG-001",
        source_type=SourceType.ADAPTIVE_FRICTION,
        source_reference_id="REF-999",
        account_id="ACC-SENDER-01",
        recipient_id="ACC-RECV-02",
        amount=2500.0,
        currency="USD",
        channel=ChannelType.MOBILE_APP,
        payment_method=PaymentMethod.WIRE_TRANSFER,
        status=TransactionStatus.FLAGGED,
        device_context=DeviceContext(
            device_id="DEV-99", ip_address="198.51.100.45", user_agent="Mozilla/5.0 Chrome"
        ),
        source_metadata={
            "af_metrics": {
                "stored_device": {"browser": "Firefox", "ip_address": "10.0.0.1"},
                "distance_km": 1200.0,
                "historical_mean_amount": 1000.0,
            },
            "ff_metrics": {
                "in_degree": 10,
                "out_degree": 10,
                "total_sent": 2500.0,
                "retained_balance": 25.0,
                "holding_minutes": 5.0,
            },
            "ph_metrics": {
                "domain_age_days": 18.0,
                "self_signed": True,
                "local_listing": "blacklist",
            },
        },
    )

    eval_res = evaluate_all_signals(canonical_tx)

    assert eval_res.transaction_id == "TX-INTEG-001"
    assert "AF" in eval_res.signal_groups
    assert "FF" in eval_res.signal_groups
    assert "PH" in eval_res.signal_groups

    # AF checks
    af_factors = {f.signal_id: f for f in eval_res.signal_groups["AF"].factors}
    assert af_factors["AF1"].risk_factor == 1.00
    assert af_factors["AF2"].risk_factor == 0.80  # 1200/1500
    assert af_factors["AF3"].risk_factor == 1.00  # (2500-1000)/1000 = 1.5 -> clipped to 1.00

    # FF checks
    ff_factors = {f.signal_id: f for f in eval_res.signal_groups["FF"].factors}
    assert ff_factors["FF1"].risk_factor == 1.00  # 10/10
    assert ff_factors["FF2"].risk_factor == 0.99  # 1 - 25/2500
    assert ff_factors["FF3"].risk_factor == 0.9167  # round(1 - 5/60, 4)

    # PH checks
    ph_factors = {f.signal_id: f for f in eval_res.signal_groups["PH"].factors}
    assert ph_factors["PH1"].risk_factor == 0.90  # 1 - 18/180
    assert ph_factors["PH2"].risk_factor == 1.00  # self-signed
    assert ph_factors["PH3"].risk_factor == 1.00  # blacklist


def test_signals_evaluate_api_endpoint(test_client: TestClient) -> None:
    payload = {
        "transaction": {
            "transaction_id": "TX-API-EVAL-1",
            "account_id": "ACC-API-1",
            "recipient_id": "ACC-API-2",
            "amount": 500.0,
            "currency": "USD",
            "channel": "WEB",
            "payment_method": "CREDIT_CARD",
            "status": "PENDING",
            "device_context": {"ip_address": "1.2.3.4", "is_vpn": True},
        },
        "custom_metrics": {
            "distance_km": 750.0,
            "historical_mean_amount": 250.0,
            "in_degree": 5,
            "out_degree": 5,
            "domain_age_days": 90.0,
        },
    }

    response = test_client.post("/api/v1/signals/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["transaction_id"] == "TX-API-EVAL-1"
    assert "AF" in data["signal_groups"]
    assert "FF" in data["signal_groups"]
    assert "PH" in data["signal_groups"]
    assert len(data["signal_groups"]["AF"]["factors"]) == 3
