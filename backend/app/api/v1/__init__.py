"""API v1 router assembly."""

from fastapi import APIRouter

from app.api.v1.config import router as config_router
from app.api.v1.health import router as health_router
from app.api.v1.ingest import router as ingest_router
from app.api.v1.signals import router as signals_router

router = APIRouter(prefix="/v1")
router.include_router(health_router, tags=["Health"])
router.include_router(config_router, tags=["Configuration"])
router.include_router(ingest_router, tags=["Ingestion"])
router.include_router(signals_router, tags=["Signal Engines"])


