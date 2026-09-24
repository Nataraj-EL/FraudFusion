from abc import ABC, abstractmethod
from typing import Any

from app.schemas.ingestion import SourceType, ValidationErrorItem


class BaseParser(ABC):
    """Abstract interface for modular data source parsers."""

    @property
    @abstractmethod
    def source_type(self) -> SourceType:
        """Returns the signal source domain type handled by this parser."""
        pass

    @abstractmethod
    def parse(
        self, content: str | bytes, filename: str = "upload"
    ) -> tuple[list[dict[str, Any]], list[ValidationErrorItem]]:
        """
        Parses raw string or bytes input.
        Returns tuple of (parsed_raw_records, syntax_parse_errors).
        """
        pass
