from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter

from app import __version__
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=dict[str, Any])
async def health_check() -> dict[str, Any]:
    """Health check endpoint exposing system status and metadata."""
    return {
        "status": "ok",
        "service": "FraudFusion API",
        "version": __version__,
        "environment": settings.environment,
        "timestamp": datetime.now(UTC).isoformat(),
    }
