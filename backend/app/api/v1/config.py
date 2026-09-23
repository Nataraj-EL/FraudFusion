from typing import Any

from fastapi import APIRouter

from app.core.config import load_risk_config, settings

router = APIRouter()


@router.get("/config", response_model=dict[str, Any])
async def get_frontend_config() -> dict[str, Any]:
    """Exposes minimal, frontend-safe risk weights and band definitions for the UI."""
    config = load_risk_config(settings.risk_config_path)

    signal_groups = [
        {
            "code": group.code,
            "name": group.name,
            "weight": group.weight,
            "description": group.description,
        }
        for group in config.signal_groups.values()
    ]

    risk_bands = [
        {
            "band": band.band,
            "min_score": band.min_score,
            "max_score": band.max_score,
            "action": band.action,
            "color": band.color,
        }
        for band in config.risk_bands
    ]

    return {
        "version": config.version,
        "signal_groups": signal_groups,
        "risk_bands": risk_bands,
    }
