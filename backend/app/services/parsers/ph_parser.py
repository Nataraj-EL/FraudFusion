import json
from typing import Any

from app.schemas.ingestion import SourceType, ValidationErrorItem
from app.services.parsers.base import BaseParser


class PhishingParser(BaseParser):
    """Parser for Phishing Site JSON files."""

    @property
    def source_type(self) -> SourceType:
        return SourceType.PHISHING

    def parse(
        self, content: str | bytes, filename: str = "ph_upload.json"
    ) -> tuple[list[dict[str, Any]], list[ValidationErrorItem]]:
        if isinstance(content, bytes):
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError as exc:
                return [], [
                    ValidationErrorItem(
                        record_index=0,
                        field="encoding",
                        reason=f"File content must be UTF-8 encoded text: {exc}",
                        source_type=self.source_type,
                    )
                ]
        else:
            text = content

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            return [], [
                ValidationErrorItem(
                    record_index=0,
                    field="json_syntax",
                    reason=f"Invalid Phishing JSON syntax: line {exc.lineno}, col {exc.colno}",
                    source_type=self.source_type,
                )
            ]

        if isinstance(parsed, dict):
            return [parsed], []
        elif isinstance(parsed, list):
            records: list[dict[str, Any]] = []
            errors: list[ValidationErrorItem] = []
            for idx, item in enumerate(parsed):
                if isinstance(item, dict):
                    records.append(item)
                else:
                    errors.append(
                        ValidationErrorItem(
                            record_index=idx,
                            field="record_type",
                            reason=f"Expected JSON object, got {type(item).__name__}",
                            source_type=self.source_type,
                        )
                    )


            return records, errors
        else:
            return [], [
                ValidationErrorItem(
                    record_index=0,
                    field="json_root",
                    reason="Phishing JSON root must be an object or array of objects",
                    source_type=self.source_type,
                )
            ]
