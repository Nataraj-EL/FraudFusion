import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.ingestion import CanonicalTransaction, SourceType
from app.schemas.transaction import DeviceContext, Transaction
from app.services.risk_engine import (
    _determine_risk_band_and_action,
    evaluate_risk_score,
)


def test_determine_risk_band_and_action():
    """Verify dynamic mapping of scores [0, 100] to risk bands and recommended actions."""
    assert _determine_risk_band_and_action(0.0) == ("Very Low", "ALLOW")
    assert _determine_risk_band_and_action(15.0) == ("Very Low", "ALLOW")
    assert _determine_risk_band_and_action(20.0) == ("Very Low", "ALLOW")

    assert _determine_risk_band_and_action(21.0) == ("Low", "MONITOR")
    assert _determine_risk_band_and_action(35.0) == ("Low", "MONITOR")
    assert _determine_risk_band_and_action(40.0) == ("Low", "MONITOR")

    assert _determine_risk_band_and_action(41.0) == ("Medium", "CHALLENGE")
    assert _determine_risk_band_and_action(55.0) == ("Medium", "CHALLENGE")
    assert _determine_risk_band_and_action(60.0) == ("Medium", "CHALLENGE")

    assert _determine_risk_band_and_action(61.0) == ("High", "HOLD")
    assert _determine_risk_band_and_action(75.0) == ("High", "HOLD")
    assert _determine_risk_band_and_action(80.0) == ("High", "HOLD")

    assert _determine_risk_band_and_action(81.0) == ("Critical", "BLOCK_AND_REPORT")
    assert _determine_risk_band_and_action(95.0) == ("Critical", "BLOCK_AND_REPORT")
    assert _determine_risk_band_and_action(100.0) == ("Critical", "BLOCK_AND_REPORT")


def test_exact_weighted_consolidation():
    """
    Verify exact formula:
    Risk Score = (AF subscore * 0.45) + (FF subscore * 0.35) + (PH subscore * 0.20)
    """
    tx = Transaction(
        transaction_id="TX-MATH-001",
        account_id="ACC-100",
        recipient_id="ACC-200",
        amount=100.0,
        currency="USD",
    )
    # AF: AF1=1.0 (wt 0.5), AF2=1.0 (wt 0.3), AF3=1.0 (wt 0.2) => raw AF = 1.0 => AF subscore = 100
    # FF: all 0 => raw FF = 0.0 => FF subscore = 0.0
    # PH: all 0 => raw PH = 0.0 => PH subscore = 0.0

    custom_metrics = {
        "device_fingerprint_changed": True,
        "distance_km": 1500.0,
        "historical_mean_amount": 10.0,  # ratio (100-10)/10 = 9 >= 1.0 => 1.0
        "retained_balance": 1000.0,
        "total_sent": 1000.0,
        "domain_age_days": 365.0,
        "self_signed": False,
        "local_listing": "clean",
    }

    res = evaluate_risk_score(tx, custom_metrics)

    assert res.af_subscore == 100.0
    assert res.ff_subscore == 0.0
    assert res.ph_subscore == 0.0
    # Score = 100.0 * 0.45 + 0 * 0.35 + 0 * 0.20 = 45.0
    assert res.consolidated_score == 45.0
    assert res.risk_score == 45.0
    assert res.risk_band == "Medium"
    assert res.recommended_action == "CHALLENGE"


def test_zero_and_clean_edge_case():
    """Verify clean transaction produces 0.0 score, Very Low band, and ALLOW action."""
    tx = Transaction(
        transaction_id="TX-CLEAN-001",
        account_id="ACC-CLEAN",
        recipient_id="ACC-RECV",
        amount=50.0,
        currency="USD",
        device_context=DeviceContext(user_agent="Firefox", ip_address="192.168.1.1"),
    )
    custom_metrics = {
        "stored_device": {"user_agent": "Firefox", "ip_address": "192.168.1.1"},
        "distance_km": 0.0,
        "historical_mean_amount": 100.0,
        "in_degree": 0,
        "out_degree": 2,
        "retained_balance": 5000.0,
        "total_sent": 100.0,
        "holding_minutes": 1440.0,
        "domain_age_days": 365.0,
        "self_signed": False,
        "local_listing": "clean",
    }

    res = evaluate_risk_score(tx, custom_metrics)
    assert res.af_subscore == 0.0
    assert res.ff_subscore == 0.0
    assert res.ph_subscore == 0.0
    assert res.consolidated_score == 0.0
    assert res.risk_band == "Very Low"
    assert res.recommended_action == "ALLOW"
    assert "no anomalies" in res.explanation.lower()


def test_max_critical_risk_scenario():
    """
    Verify maximum anomaly flags across AF, FF, PH produce 100.0 score,
    Critical band, and BLOCK action.
    """

    tx = Transaction(
        transaction_id="TX-CRIT-999",
        account_id="ACC-BAD",
        recipient_id="ACC-DEST",
        amount=5000.0,
        currency="USD",
    )
    custom_metrics = {
        "device_fingerprint_changed": True,
        "distance_km": 3000.0,
        "historical_mean_amount": 100.0,
        "in_degree": 10,
        "out_degree": 10,
        "retained_balance": 0.0,
        "total_sent": 5000.0,
        "holding_minutes": 0.0,
        "domain_age_days": 0.0,
        "self_signed": True,
        "local_listing": "blacklist",
    }

    res = evaluate_risk_score(tx, custom_metrics)
    assert res.af_subscore == 100.0
    assert res.ff_subscore == 100.0
    assert res.ph_subscore == 100.0
    assert res.consolidated_score == 100.0
    assert res.risk_band == "Critical"
    assert res.recommended_action == "BLOCK_AND_REPORT"
    assert res.str_report_eligible is True
    assert len(res.triggered_signals) == 9


def test_clipping_bounds():
    """Ensure score clipping strictly maintains [0.0, 100.0] bounds."""
    tx = Transaction(
        transaction_id="TX-CLIP-001", account_id="ACC-1", recipient_id="ACC-2", amount=10.0
    )
    res = evaluate_risk_score(tx)
    assert 0.0 <= res.consolidated_score <= 100.0
    assert 0.0 <= res.af_subscore <= 100.0
    assert 0.0 <= res.ff_subscore <= 100.0
    assert 0.0 <= res.ph_subscore <= 100.0


def test_explainability_phrase_generation():
    """Verify deterministic concise driver text matching spec examples."""
    tx = Transaction(
        transaction_id="TX-EXP-001", account_id="ACC-EXP", recipient_id="ACC-DEST", amount=2000.0
    )
    custom_metrics = {
        "device_fingerprint_changed": True,
        "retained_balance": 0.0,
        "total_sent": 2000.0,
        "holding_minutes": 60.0,
    }

    res = evaluate_risk_score(tx, custom_metrics)
    # AF1 triggered (device fingerprint change) and FF2 triggered (near-zero retained balance)
    assert "device fingerprint change" in res.explanation
    assert "near-zero retained balance" in res.explanation
    assert "primarily driven by" in res.explanation


def test_end_to_end_canonical_transaction_evaluation():
    """Verify full end-to-end evaluation using a CanonicalTransaction model."""
    can_tx = CanonicalTransaction(
        transaction_id="CAN-TX-500",
        source_type=SourceType.ADAPTIVE_FRICTION,
        source_reference_id="REF-500",
        account_id="ACC-500",
        recipient_id="ACC-501",
        amount=1500.0,
        currency="USD",
        source_metadata={
            "af_metrics": {
                "distance_km": 1500.0,
                "historical_mean_amount": 500.0,
            }
        },
    )

    res = evaluate_risk_score(can_tx)
    assert res.transaction_id == "CAN-TX-500"
    assert res.af_subscore > 0.0
    assert "AF" in res.all_signal_results
    assert "FF" in res.all_signal_results
    assert "PH" in res.all_signal_results


@pytest.mark.asyncio
async def test_risk_score_api_endpoint():
    """Test POST /api/v1/risk-score endpoint with valid JSON payload."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        payload = {
            "transaction": {
                "transaction_id": "TX-API-777",
                "account_id": "ACC-API",
                "recipient_id": "ACC-RECV-777",
                "amount": 1200.0,
                "currency": "USD",
                "channel": "MOBILE_APP",
            },
            "custom_metrics": {
                "device_fingerprint_changed": True,
                "distance_km": 800.0,
                "domain_age_days": 10.0,
            },
        }


        response = await client.post("/api/v1/risk-score", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["transaction_id"] == "TX-API-777"
        assert "af_subscore" in data
        assert "ff_subscore" in data
        assert "ph_subscore" in data
        assert "consolidated_score" in data
        assert "risk_band" in data
        assert "recommended_action" in data
        assert "explanation" in data
        assert "triggered_signals" in data
        assert "all_signal_results" in data
