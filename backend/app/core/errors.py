from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse


class FraudFusionError(Exception):
    """Base domain exception for FraudFusion."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigValidationError(FraudFusionError):
    """Raised when configuration files fail validation rules."""

    pass


class InvalidWeightError(ConfigValidationError):
    """Raised when signal weights do not sum to 1.0."""

    pass


class InvalidRiskBandError(ConfigValidationError):
    """Raised when risk band boundaries are invalid or non-contiguous."""

    pass


async def fraud_fusion_exception_handler(
    request: Request, exc: FraudFusionError
) -> JSONResponse:
    """Global HTTP exception handler for domain errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global HTTP fallback exception handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred on the server.",
        },
    )
