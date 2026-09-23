from fastapi.testclient import TestClient


def test_health_endpoint(test_client: TestClient) -> None:
    """Test GET /api/v1/health status and payload."""
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "FraudFusion API"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data


def test_config_endpoint(test_client: TestClient) -> None:
    """Test GET /api/v1/config frontend-safe configuration endpoint."""
    response = test_client.get("/api/v1/config")
    assert response.status_code == 200

    data = response.json()
    assert "version" in data
    assert "signal_groups" in data
    assert "risk_bands" in data

    # Verify 3 signal groups (AF 0.45, FF 0.35, PH 0.20)
    groups = {g["code"]: g for g in data["signal_groups"]}
    assert len(groups) == 3
    assert groups["AF"]["weight"] == 0.45
    assert groups["FF"]["weight"] == 0.35
    assert groups["PH"]["weight"] == 0.20

    # Verify 5 risk bands
    bands = data["risk_bands"]
    assert len(bands) == 5
    assert bands[0]["band"] == "Very Low"
    assert bands[0]["min_score"] == 0
    assert bands[0]["max_score"] == 20
    assert bands[-1]["band"] == "Critical"
    assert bands[-1]["min_score"] == 81
    assert bands[-1]["max_score"] == 100
