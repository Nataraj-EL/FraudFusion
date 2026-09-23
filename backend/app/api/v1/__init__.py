"""API v1 router assembly."""

from fastapi import APIRouter

from app.api.v1.config import router as config_router
from app.api.v1.health import router as health_router

router = APIRouter(prefix="/v1")
router.include_router(health_router, tags=["Health"])
router.include_router(config_router, tags=["Configuration"])
