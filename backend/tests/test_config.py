from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.core.config import RiskConfig, load_risk_config
from app.core.errors import ConfigValidationError, InvalidRiskBandError, InvalidWeightError


def test_valid_config_loading() -> None:
    """Test loading default production YAML configuration."""
    config_path = Path("config/risk_config.yaml")
    config = load_risk_config(config_path)

    assert isinstance(config, RiskConfig)
    assert len(config.signal_groups) == 3
    assert "adaptive_friction" in config.signal_groups
    assert config.signal_groups["adaptive_friction"].weight == 0.45
    assert config.signal_groups["fund_flow"].weight == 0.35
    assert config.signal_groups["phishing"].weight == 0.20
    assert len(config.risk_bands) == 5
    assert config.risk_bands[0].band == "Very Low"
    assert config.risk_bands[-1].band == "Critical"


def test_weight_sum_validation_failure(
    temp_yaml_factory: Any, valid_config_dict: dict[str, Any]
) -> None:
    """Test error when weights do not sum to 1.0."""
    valid_config_dict["signal_groups"]["adaptive_friction"]["weight"] = 0.60
    # Sum is now 0.60 + 0.35 + 0.20 = 1.15
    tmp_path = temp_yaml_factory(valid_config_dict)

    with pytest.raises((InvalidWeightError, ValidationError)):
        load_risk_config(tmp_path)


def test_risk_band_gap_validation_failure(
    temp_yaml_factory: Any, valid_config_dict: dict[str, Any]
) -> None:
    """Test error when risk bands contain a gap."""
    valid_config_dict["risk_bands"][0]["max_score"] = 15  # Gap between 15 and 21
    tmp_path = temp_yaml_factory(valid_config_dict)

    with pytest.raises((InvalidRiskBandError, ValidationError)):
        load_risk_config(tmp_path)


def test_risk_band_start_not_zero_failure(
    temp_yaml_factory: Any, valid_config_dict: dict[str, Any]
) -> None:
    """Test error when lowest risk band does not start at 0."""
    valid_config_dict["risk_bands"][0]["min_score"] = 5
    tmp_path = temp_yaml_factory(valid_config_dict)

    with pytest.raises((InvalidRiskBandError, ValidationError)):
        load_risk_config(tmp_path)


def test_risk_band_end_not_100_failure(
    temp_yaml_factory: Any, valid_config_dict: dict[str, Any]
) -> None:
    """Test error when highest risk band does not end at 100."""
    valid_config_dict["risk_bands"][-1]["max_score"] = 90
    tmp_path = temp_yaml_factory(valid_config_dict)

    with pytest.raises((InvalidRiskBandError, ValidationError)):
        load_risk_config(tmp_path)


def test_missing_config_file() -> None:
    """Test error when YAML configuration file does not exist."""
    with pytest.raises(ConfigValidationError) as exc_info:
        load_risk_config("config/non_existent_file.yaml")
    assert "not found" in str(exc_info.value).lower()


def test_invalid_yaml_syntax(temp_yaml_factory: Any) -> None:
    """Test error handling for malformed YAML files."""
    bad_yaml = "signal_groups: [invalid yaml structure: {"
    tmp_path = temp_yaml_factory(bad_yaml)

    with pytest.raises(ConfigValidationError) as exc_info:
        load_risk_config(tmp_path)
    assert "syntax" in str(exc_info.value).lower() or "yaml" in str(exc_info.value).lower()
