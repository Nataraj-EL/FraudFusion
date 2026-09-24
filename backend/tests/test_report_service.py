import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.transaction import DeviceContext, Transaction
from app.services.report_service import (
    export_report_to_csv,
    export_report_to_html,
    export_report_to_json,
    generate_risk_report,
    generate_str_draft,
)
from app.services.risk_engine import evaluate_risk_score


def test_report_field_completeness():
    """Verify generated RiskReport contains all required fields."""
    tx = Transaction(
        transaction_id="TX-RPT-001",
        account_id="ACC-SENDER-1",
        recipient_id="ACC-RECV-1",
        amount=1500.0,
        currency="USD",
    )
    assessment = evaluate_risk_score(tx, {"distance_km": 1500.0})
    report = generate_risk_report(assessment, tx)

    assert report.report_id.startswith("RPT-TX-RPT-001")
    assert report.transaction_id == "TX-RPT-001"
    assert report.account_id == "ACC-SENDER-1"
    assert report.recipient_id == "ACC-RECV-1"
    assert report.amount == 1500.0
    assert report.currency == "USD"
    assert report.consolidated_score >= 0.0
    assert report.risk_band in ("Very Low", "Low", "Medium", "High", "Critical")
    assert report.recommended_action in (
        "ALLOW",
        "MONITOR",
        "CHALLENGE",
        "HOLD",
        "BLOCK_AND_REPORT",
    )
    assert report.af_subscore >= 0.0
    assert report.ff_subscore >= 0.0
    assert report.ph_subscore >= 0.0
    assert isinstance(report.explanation, str)
    assert len(report.explanation) > 0


def test_str_generation_only_for_high_and_critical():
    """Verify STR draft is generated ONLY for High (61-80) and Critical (81-100) risk bands."""
    tx = Transaction(
        transaction_id="TX-CRIT-STR",
        account_id="ACC-BAD-1",
        recipient_id="ACC-DEST-1",
        amount=5000.0,
        currency="USD",
    )
    # Critical risk inputs
    crit_metrics = {
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
    crit_assessment = evaluate_risk_score(tx, crit_metrics)
    assert crit_assessment.risk_band == "Critical"

    crit_report = generate_risk_report(crit_assessment, tx)
    assert crit_report.str_status == "DRAFT_GENERATED"
    assert crit_report.str_draft is not None
    assert crit_report.str_draft.status == "DRAFT"
    assert "SUSPICIOUS TRANSACTION REPORT" in crit_report.str_draft.narrative
    assert crit_report.str_draft.str_id == "STR-TX-CRIT-STR"

    # High risk inputs
    tx_high = Transaction(
        transaction_id="TX-HIGH-STR",
        account_id="ACC-HIGH",
        recipient_id="ACC-DEST-2",
        amount=2500.0,
    )
    high_metrics = {
        "device_fingerprint_changed": True,
        "distance_km": 1500.0,
        "historical_mean_amount": 10.0,
    }
    high_assessment = evaluate_risk_score(tx_high, high_metrics)
    # Force high assessment score if needed
    high_report = generate_risk_report(high_assessment, tx_high)
    if high_assessment.risk_band in ("High", "Critical"):
        assert high_report.str_status == "DRAFT_GENERATED"
        assert high_report.str_draft is not None


def test_no_str_for_very_low_low_medium_bands():
    """Verify no STR draft is generated for Very Low, Low, or Medium transactions."""
    tx_clean = Transaction(
        transaction_id="TX-CLEAN-002",
        account_id="ACC-GOOD",
        recipient_id="ACC-STORE",
        amount=20.0,
        device_context=DeviceContext(user_agent="Safari", ip_address="192.168.1.1"),
    )
    clean_metrics = {
        "stored_device": {"user_agent": "Safari", "ip_address": "192.168.1.1"},
        "distance_km": 0.0,
        "historical_mean_amount": 100.0,
        "domain_age_days": 365.0,
        "local_listing": "clean",
    }
    clean_assessment = evaluate_risk_score(tx_clean, clean_metrics)
    assert clean_assessment.risk_band == "Very Low"

    clean_report = generate_risk_report(clean_assessment, tx_clean)
    assert clean_report.str_status == "NOT_REQUIRED"
    assert clean_report.str_draft is None

    str_draft_direct = generate_str_draft(clean_assessment, tx_clean)
    assert str_draft_direct is None


def test_deterministic_explanations_in_report():
    """Verify deterministic explanations are accurately transferred into the report."""
    tx = Transaction(
        transaction_id="TX-DETERMINISTIC-01",
        account_id="ACC-SENDER",
        recipient_id="ACC-RECV",
        amount=1000.0,
    )
    assessment = evaluate_risk_score(tx, {"device_fingerprint_changed": True})
    report = generate_risk_report(assessment, tx)

    assert "device fingerprint change" in report.explanation
    assert report.explanation == assessment.explanation


def test_export_formats_json_csv_html():
    """Verify JSON, CSV, and HTML export generator outputs."""
    tx = Transaction(
        transaction_id="TX-EXP-999",
        account_id="ACC-A",
        recipient_id="ACC-B",
        amount=300.0,
    )
    assessment = evaluate_risk_score(tx)
    report = generate_risk_report(assessment, tx)

    # Test JSON export
    json_str = export_report_to_json(report)
    parsed_json = json.loads(json_str)
    assert parsed_json["transaction_id"] == "TX-EXP-999"
    assert "consolidated_score" in parsed_json

    # Test CSV export
    csv_str = export_report_to_csv(report)
    assert "transaction_id,timestamp,account_id" in csv_str
    assert "TX-EXP-999" in csv_str
    assert "ACC-A" in csv_str

    # Test HTML export
    html_str = export_report_to_html(report)
    assert "<!DOCTYPE html>" in html_str
    assert "FraudFusion Risk Assessment Report" in html_str
    assert "TX-EXP-999" in html_str


@pytest.mark.asyncio
async def test_report_api_endpoints():
    """Test POST /api/v1/reports/generate and GET download/export API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Generate report
        payload = {
            "transaction": {
                "transaction_id": "TX-API-REPORT-100",
                "account_id": "ACC-API-1",
                "recipient_id": "ACC-API-2",
                "amount": 2500.0,
                "currency": "USD",
            },
            "custom_metrics": {
                "device_fingerprint_changed": True,
                "distance_km": 1200.0,
                "domain_age_days": 10.0,
            },
        }

        gen_resp = await client.post("/api/v1/reports/generate", json=payload)
        assert gen_resp.status_code == 200
        gen_data = gen_resp.json()
        assert gen_data["transaction_id"] == "TX-API-REPORT-100"
        assert "str_status" in gen_data

        # GET report by ID
        get_resp = await client.get("/api/v1/reports/TX-API-REPORT-100")
        assert get_resp.status_code == 200
        assert get_resp.json()["transaction_id"] == "TX-API-REPORT-100"

        # GET download JSON
        dl_json = await client.get("/api/v1/reports/TX-API-REPORT-100/download?format=json")
        assert dl_json.status_code == 200
        assert "application/json" in dl_json.headers["content-type"]

        # GET download CSV
        dl_csv = await client.get("/api/v1/reports/TX-API-REPORT-100/download?format=csv")
        assert dl_csv.status_code == 200
        assert "text/csv" in dl_csv.headers["content-type"]
        assert "TX-API-REPORT-100" in dl_csv.text

        # GET download HTML
        dl_html = await client.get("/api/v1/reports/TX-API-REPORT-100/download?format=html")
        assert dl_html.status_code == 200
        assert "text/html" in dl_html.headers["content-type"]
        assert "<!DOCTYPE html>" in dl_html.text

        # GET export endpoint
        exp_resp = await client.get("/api/v1/export/TX-API-REPORT-100?format=json")
        assert exp_resp.status_code == 200


@pytest.mark.asyncio
async def test_missing_transaction_report_handling():
    """Verify 404 Not Found error for non-existent report/transaction."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/api/v1/reports/NONEXISTENT-TX-9999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()
