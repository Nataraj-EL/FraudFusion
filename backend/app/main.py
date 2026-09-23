from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.errors import (
    FraudFusionError,
    fraud_fusion_exception_handler,
    generic_exception_handler,
)
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    logger.info(
        f"Starting FraudFusion API v{__version__} in [{settings.environment}] environment"
    )
    yield
    logger.info("Shutting down FraudFusion API")


app = FastAPI(
    title="FraudFusion API",
    description="Unified, Explainable Fraud Detection Platform API",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(FraudFusionError, fraud_fusion_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API Router
app.include_router(api_v1_router, prefix="/api")

