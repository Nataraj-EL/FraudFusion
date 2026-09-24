import tempfile

import pytest
from fastapi.testclient import TestClient

from app.core.database import init_db


@pytest.fixture
def temp_db_setup(monkeypatch: pytest.MonkeyPatch) -> str:
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    init_db(tmp.name)
    monkeypatch.setattr("app.core.config.settings.database_path", tmp.name)
    return tmp.name


def test_ingest_upload_api_json(test_client: TestClient, temp_db_setup: str) -> None:
    json_payload = """[
        {"af_id": "AF-API-1", "account_id": "U1", "recipient_id": "U2", "amount": 90.0},
        {"af_id": "AF-API-2", "account_id": "U3", "recipient_id": "U4", "amount": 0.0}
    ]"""

    response = test_client.post(
        "/api/v1/ingest/upload",
        files={"file": ("adaptive_friction_test.json", json_payload, "application/json")},
        data={"source_type": "ADAPTIVE_FRICTION"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "batch" in data
    assert data["batch"]["source_type"] == "ADAPTIVE_FRICTION"
    assert data["batch"]["accepted_count"] == 1
    assert data["batch"]["rejected_count"] == 1
    assert len(data["validation_errors"]) == 1
    assert data["validation_errors"][0]["reference_id"] == "AF-API-2"


def test_ingest_upload_api_csv(test_client: TestClient, temp_db_setup: str) -> None:
    csv_payload = """transaction_id,sender_account_id,recipient_account_id,amount,currency
TX-CSV-1,ACC-1,ACC-2,500.0,USD
"""

    response = test_client.post(
        "/api/v1/ingest/upload",
        files={"file": ("fund_flow.csv", csv_payload, "text/csv")},
        data={"source_type": "FUND_FLOW"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["batch"]["accepted_count"] == 1
    assert data["batch"]["rejected_count"] == 0


def test_list_batches_api(test_client: TestClient, temp_db_setup: str) -> None:
    response = test_client.get("/api/v1/ingest/batches")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
