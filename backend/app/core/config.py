import math
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.errors import ConfigValidationError, InvalidRiskBandError, InvalidWeightError


class SignalGroupConfig(BaseModel):
    code: str
    name: str
    weight: float = Field(..., ge=0.0, le=1.0)
    description: str


class FactorClippingConfig(BaseModel):
    min_value: float = 0.0
    max_value: float = 1.0

    @field_validator("max_value")
    @classmethod
    def check_min_less_than_max(cls, v: float, info: Any) -> float:
        min_val = info.data.get("min_value", 0.0)
        if v <= min_val:
            raise ConfigValidationError(
                f"max_value ({v}) must be greater than min_value ({min_val})"
            )
        return v


class RiskBandConfig(BaseModel):
    band: str
    min_score: int = Field(..., ge=0, le=100)
    max_score: int = Field(..., ge=0, le=100)
    action: str
    color: str

    @field_validator("max_score")
    @classmethod
    def check_scores(cls, v: int, info: Any) -> int:
        min_s = info.data.get("min_score", 0)
        if v < min_s:
            raise InvalidRiskBandError(
                f"Risk band max_score ({v}) cannot be less than min_score ({min_s})"
            )
        return v


class RiskConfig(BaseModel):
    version: str = "1.0"
    description: str = "Unified fraud risk weights and band thresholds"
    signal_groups: dict[str, SignalGroupConfig]
    factor_clipping: FactorClippingConfig = Field(default_factory=FactorClippingConfig)
    risk_bands: list[RiskBandConfig]

    @field_validator("signal_groups")
    @classmethod
    def validate_weights_sum(
        cls, groups: dict[str, SignalGroupConfig]
    ) -> dict[str, SignalGroupConfig]:
        if not groups:
            raise ConfigValidationError("At least one signal group must be defined")
        total_weight = sum(group.weight for group in groups.values())
        if not math.isclose(total_weight, 1.0, rel_tol=1e-5):
            raise InvalidWeightError(
                f"Signal group weights must sum to 1.0, got {total_weight:.4f}",
                details={"weights": {k: v.weight for k, v in groups.items()}},
            )
        return groups

    @field_validator("risk_bands")
    @classmethod
    def validate_risk_bands(cls, bands: list[RiskBandConfig]) -> list[RiskBandConfig]:
        if not bands:
            raise InvalidRiskBandError("At least one risk band must be configured")
        sorted_bands = sorted(bands, key=lambda b: b.min_score)

        if sorted_bands[0].min_score != 0:
            raise InvalidRiskBandError(
                f"Lowest risk band must start at 0, got {sorted_bands[0].min_score}"
            )
        if sorted_bands[-1].max_score != 100:
            raise InvalidRiskBandError(
                f"Highest risk band must end at 100, got {sorted_bands[-1].max_score}"
            )

        for i in range(len(sorted_bands) - 1):
            curr = sorted_bands[i]
            next_b = sorted_bands[i + 1]
            if next_b.min_score != curr.max_score + 1:
                raise InvalidRiskBandError(
                    f"Gap or overlap between bands '{curr.band}' "
                    f"({curr.min_score}-{curr.max_score}) and '{next_b.band}' "
                    f"({next_b.min_score}-{next_b.max_score})"
                )
        return bands



class Settings(BaseSettings):
    environment: str = "development"
    log_level: str = "INFO"
    host: str = "127.0.0.1"
    port: int = 8000
    risk_config_path: str = "config/risk_config.yaml"
    database_path: str = "data/fraud_fusion.db"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )



def load_risk_config(config_path: str | Path) -> RiskConfig:
    """Loads and validates the risk configuration YAML file."""
    path = Path(config_path)
    if not path.is_absolute():
        # Resolve relative to backend root directory
        base_dir = Path(__file__).resolve().parent.parent.parent
        path = base_dir / config_path

    if not path.exists():
        raise ConfigValidationError(
            f"Risk configuration file not found at path: {path}",
            details={"path": str(path)},
        )

    try:
        with open(path, encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ConfigValidationError(
            f"Invalid YAML syntax in configuration file: {exc}"
        ) from exc

    if not isinstance(raw_data, dict):
        raise ConfigValidationError("YAML configuration root must be a mapping/object")

    return RiskConfig(**raw_data)


settings = Settings()
