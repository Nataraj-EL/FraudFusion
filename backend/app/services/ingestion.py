import uuid
from datetime import UTC, datetime

from app.core.logging import logger
from app.schemas.ingestion import (
    CanonicalTransaction,
    IngestionBatchSummary,
    IngestionResult,
    SourceType,
    ValidationErrorItem,
)
from app.services.parsers.factory import auto_detect_source_type, get_parser
from app.services.persistence import get_batch_details, get_recent_batches, save_ingestion_result
from app.services.validator import validate_and_normalize_record


class IngestionService:
    """Service orchestrating raw data parsing, validation, normalization, and persistence."""

    def ingest_file(
        self,
        content: bytes | str,
        filename: str,
        source_type: SourceType | str | None = None,
    ) -> IngestionResult:
        """
        Parses, validates, normalizes, and persists an uploaded data file.
        Returns complete IngestionResult containing summary, accepted records, and errors.
        """
        # Resolve source type
        if isinstance(source_type, str):
            try:
                source_type = SourceType(source_type.upper())
            except ValueError:
                source_type = None

        if source_type is None:
            source_type = auto_detect_source_type(filename, content)

        batch_id = f"batch_{uuid.uuid4().hex[:12]}"
        logger.info(
            f"Starting ingestion batch [{batch_id}] for source "
            f"'{source_type.value}' filename '{filename}'"
        )

        parser = get_parser(source_type)
        raw_records, parse_errors = parser.parse(content, filename)

        validation_errors: list[ValidationErrorItem] = list(parse_errors)
        accepted_records: list[CanonicalTransaction] = []

        for idx, raw_rec in enumerate(raw_records):
            tx, record_errors = validate_and_normalize_record(raw_rec, idx, source_type)
            if record_errors:
                validation_errors.extend(record_errors)
            elif tx:
                accepted_records.append(tx)

        # Calculate counts
        rejected_indices = {err.record_index for err in validation_errors}
        rejected_count = len(rejected_indices)
        total_records = len(raw_records) if raw_records else rejected_count
        accepted_count = len(accepted_records)

        summary = IngestionBatchSummary(
            batch_id=batch_id,
            source_type=source_type,
            filename=filename,
            total_records=total_records,
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            created_at=datetime.now(UTC),
        )

        result = IngestionResult(
            batch=summary,
            accepted_records=accepted_records,
            validation_errors=validation_errors,
        )

        # Persist to SQLite
        save_ingestion_result(result)

        logger.info(
            f"Completed ingestion batch [{batch_id}]: {accepted_count} accepted, "
            f"{rejected_count} rejected out of {total_records} total"
        )
        return result


    def list_batches(self, limit: int = 50) -> list[IngestionBatchSummary]:
        return get_recent_batches(limit)

    def get_batch(self, batch_id: str) -> IngestionResult | None:
        return get_batch_details(batch_id)


ingestion_service = IngestionService()
