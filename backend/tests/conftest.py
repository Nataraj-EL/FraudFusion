import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def valid_config_dict() -> dict[str, Any]:
    return {
        "version": "1.0",
        "description": "Test risk configuration",
        "signal_groups": {
            "adaptive_friction": {
                "code": "AF",
                "name": "Adaptive Friction",
                "weight": 0.45,
                "description": "Test AF",
            },
            "fund_flow": {
                "code": "FF",
                "name": "Fund Flow",
                "weight": 0.35,
                "description": "Test FF",
            },
            "phishing": {
                "code": "PH",
                "name": "Phishing",
                "weight": 0.20,
                "description": "Test PH",
            },
        },
        "factor_clipping": {"min_value": 0.0, "max_value": 1.0},
        "risk_bands": [
            {
                "band": "Very Low",
                "min_score": 0,
                "max_score": 20,
                "action": "ALLOW",
                "color": "#10b981",
            },
            {
                "band": "Low",
                "min_score": 21,
                "max_score": 40,
                "action": "MONITOR",
                "color": "#3b82f6",
            },
            {
                "band": "Medium",
                "min_score": 41,
                "max_score": 60,
                "action": "CHALLENGE",
                "color": "#f59e0b",
            },
            {
                "band": "High",
                "min_score": 61,
                "max_score": 80,
                "action": "HOLD",
                "color": "#ef4444",
            },
            {
                "band": "Critical",
                "min_score": 81,
                "max_score": 100,
                "action": "BLOCK_AND_REPORT",
                "color": "#991b1b",
            },
        ],
    }


@pytest.fixture
def temp_yaml_factory() -> Generator[Any]:
    created_files: list[Path] = []

    def _create_file(content: dict[str, Any] | str) -> Path:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        )
        if isinstance(content, dict):
            yaml.dump(content, tmp)
        else:
            tmp.write(content)
        tmp.close()
        path = Path(tmp.name)
        created_files.append(path)
        return path

    yield _create_file

    for p in created_files:
        if p.exists():
            p.unlink()
