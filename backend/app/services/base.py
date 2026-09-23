from abc import ABC, abstractmethod
from typing import Any

from app.schemas.signals import RiskAssessment, SignalGroupResult
from app.schemas.transaction import Transaction


class BaseIngestionService(ABC):
    """Abstract interface for transaction and metadata ingestion services."""

    @abstractmethod
    async def ingest_transaction(self, raw_data: dict[str, Any]) -> Transaction:
        """Validate and ingest raw transaction payload."""
        pass


class BaseSignalService(ABC):
    """Abstract interface for signal group evaluation services (AF, FF, PH)."""

    @abstractmethod
    async def evaluate_signal(self, transaction: Transaction) -> SignalGroupResult:
        """Evaluate signal group metrics for a given transaction."""
        pass


class BaseScoringEngine(ABC):
    """Abstract interface for composite risk score and band evaluation engine."""

    @abstractmethod
    async def score_transaction(self, transaction: Transaction) -> RiskAssessment:
        """Compute 0-100 score, band, action, and explanation for transaction."""
        pass
