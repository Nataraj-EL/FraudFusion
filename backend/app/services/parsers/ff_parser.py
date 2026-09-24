import csv
import io
from typing import Any

from app.schemas.ingestion import SourceType, ValidationErrorItem
from app.services.parsers.base import BaseParser


class FundFlowParser(BaseParser):
    """Parser for Fund Flow CSV files."""

    @property
    def source_type(self) -> SourceType:
        return SourceType.FUND_FLOW

    def parse(
        self, content: str | bytes, filename: str = "ff_upload.csv"
    ) -> tuple[list[dict[str, Any]], list[ValidationErrorItem]]:
        if isinstance(content, bytes):
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError as exc:
                return [], [
                    ValidationErrorItem(
                        record_index=0,
                        field="encoding",
                        reason=f"CSV content must be UTF-8 encoded: {exc}",
                        source_type=self.source_type,
                    )
                ]
        else:
            text = content

        text = text.strip()
        if not text:
            return [], [
                ValidationErrorItem(
                    record_index=0,
                    field="file_empty",
                    reason="Uploaded CSV file is empty",
                    source_type=self.source_type,
                )
            ]

        f = io.StringIO(text)
        try:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return [], [
                    ValidationErrorItem(
                        record_index=0,
                        field="csv_header",
                        reason="CSV header missing or empty",
                        source_type=self.source_type,
                    )
                ]
            records: list[dict[str, Any]] = []
            for idx, row in enumerate(reader):
                # Clean whitespace from keys and values
                clean_row = {
                    (k.strip() if k else f"col_{i}"): (v.strip() if v else None)
                    for i, (k, v) in enumerate(row.items())
                }
                records.append(clean_row)
            return records, []
        except csv.Error as exc:
            return [], [
                ValidationErrorItem(
                    record_index=0,
                    field="csv_syntax",
                    reason=f"Invalid CSV syntax: {exc}",
                    source_type=self.source_type,
                )
            ]
