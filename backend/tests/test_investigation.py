from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db_connection
from app.main import app
from app.schemas.auth import UserResponse, UserRole
from app.schemas.ingestion import (
    CanonicalTransaction,
    IngestionBatchSummary,
    IngestionResult,
    SourceType,
)
from app.schemas.transaction import ChannelType, DeviceContext, PaymentMethod, TransactionStatus
from app.services.auth_service import create_token
from app.services.persistence import save_ingestion_result

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Sets up an isolated test SQLite database for investigation endpoints."""
    db_file = str(tmp_path / "test_investigation.db")
    monkeypatch.setattr("app.core.config.settings.database_path", db_file)
    conn = get_db_connection(db_file)

    # Seed test transactions
    now = datetime.now(UTC)
    tx1 = CanonicalTransaction(
        transaction_id="TX-INV-1001",
        source_type=SourceType.FUND_FLOW,
        source_reference_id="FF-1001",
        account_id="ACC-SENDER-101",
        recipient_id="ACC-RECV-901",
        amount=5000.0,
        currency="USD",
        channel=ChannelType.WEB,
        payment_method=PaymentMethod.WIRE_TRANSFER,
        status=TransactionStatus.COMPLETED,
        timestamp=now,
        device_context=DeviceContext(ip_address="192.168.1.1", user_agent="Mozilla/5.0"),
        source_metadata={
            "ff_metrics": {
                "in_degree": 3.0,
                "out_degree": 3.0,
                "retained_balance": 0.0,
                "total_sent": 5000.0,
                "holding_minutes": 15.0,
            }
        },
    )

    tx2 = CanonicalTransaction(
        transaction_id="TX-INV-1002",
        source_type=SourceType.ADAPTIVE_FRICTION,
        source_reference_id="AF-1002",
        account_id="ACC-SENDER-102",
        recipient_id="ACC-RECV-902",
        amount=100.0,
        currency="USD",
        channel=ChannelType.MOBILE_APP,
        payment_method=PaymentMethod.CREDIT_CARD,
        status=TransactionStatus.COMPLETED,
        timestamp=now,
        device_context=DeviceContext(ip_address="10.0.0.1"),
        source_metadata={},
    )

    batch_summary = IngestionBatchSummary(
        batch_id="BATCH-TEST-INV",
        source_type=SourceType.FUND_FLOW,
        filename="test_ff.csv",
        total_records=2,
        accepted_count=2,
        rejected_count=0,
        created_at=now,
    )
    result = IngestionResult(
        batch=batch_summary,
        accepted_records=[tx1, tx2],
        validation_errors=[],
    )
    save_ingestion_result(result, conn)
    conn.close()


def get_auth_header(role: str) -> dict[str, str]:
    email = f"{role.lower()}@fraudfusion.io"
    user_resp = UserResponse(
        user_id=f"user-{role.lower()}",
        email=email,
        full_name=f"Test {role}",
        role=UserRole(role),
    )
    token = create_token(user_resp)
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_summary_empty():
    """Test dashboard summary returns structured counts."""
    headers = get_auth_header("Analyst")
    response = client.get("/api/v1/investigations/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_transactions" in data
    assert data["total_transactions"] >= 2
    assert "risk_band_counts" in data
    assert "recent_high_risk" in data
    assert "pending_investigations" in data


def test_search_and_filter_transactions():
    """Test listing and filtering transactions by search term and risk band."""
    headers = get_auth_header("Viewer")

    # Search by transaction ID
    res = client.get("/api/v1/investigations/transactions?search=TX-INV-1001", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert data["items"][0]["transaction_id"] == "TX-INV-1001"

    # Search by account ID
    url_ac = "/api/v1/investigations/transactions?account_id=ACC-SENDER-102"
    res = client.get(url_ac, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert data["items"][0]["account_id"] == "ACC-SENDER-102"

    # Empty search result
    url_empty = "/api/v1/investigations/transactions?search=NONEXISTENT_TX_ID"
    res = client.get(url_empty, headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 0
    assert len(res.json()["items"]) == 0


def test_get_investigation_detail():
    """Test retrieving full investigation detail for a single transaction."""
    headers = get_auth_header("Analyst")

    # Valid transaction
    res = client.get("/api/v1/investigations/transactions/TX-INV-1001", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["transaction"]["transaction_id"] == "TX-INV-1001"
    assert data["risk_report"] is not None
    assert data["risk_report"]["consolidated_score"] >= 0.0
    assert data["fund_flow"] is not None

    # Nonexistent transaction
    res = client.get("/api/v1/investigations/transactions/TX-INV-9999", headers=headers)
    assert res.status_code == 404


def test_fund_flow_visualization():
    """Test fund flow node and edge network topology endpoint."""
    headers = get_auth_header("Viewer")
    res = client.get("/api/v1/investigations/transactions/TX-INV-1001/fund-flow", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["transaction_id"] == "TX-INV-1001"
    assert len(data["nodes"]) >= 2
    assert len(data["edges"]) >= 1
    assert data["metrics"]["short_holding_flag"] is True


def test_rbac_unauthenticated_blocked():
    """Test unauthenticated requests are rejected."""
    res = client.get("/api/v1/investigations/summary")
    assert res.status_code == 401
