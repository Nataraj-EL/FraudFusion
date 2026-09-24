import json
import sqlite3
from datetime import UTC, datetime

from app.core.database import get_db_connection
from app.schemas.ingestion import (
    CanonicalTransaction,
    IngestionBatchSummary,
    IngestionResult,
    SourceType,
    ValidationErrorItem,
)
from app.schemas.transaction import ChannelType, DeviceContext, PaymentMethod, TransactionStatus


def save_ingestion_result(
    result: IngestionResult, conn: sqlite3.Connection | None = None
) -> None:
    """Persists ingestion batch summary, validation errors, and normalized transactions."""
    own_conn = False
    if conn is None:
        conn = get_db_connection()
        own_conn = True

    try:
        with conn:
            batch = result.batch
            conn.execute(
                """
                INSERT INTO ingestion_batches (
                    batch_id, source_type, filename, total_records,
                    accepted_count, rejected_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch.batch_id,
                    batch.source_type.value,
                    batch.filename,
                    batch.total_records,
                    batch.accepted_count,
                    batch.rejected_count,
                    batch.created_at.isoformat(),
                ),
            )

            for err in result.validation_errors:
                conn.execute(
                    """
                    INSERT INTO validation_errors (
                        batch_id, record_index, reference_id, field, reason, source_type, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        batch.batch_id,
                        err.record_index,
                        err.reference_id,
                        err.field,
                        err.reason,
                        err.source_type.value,
                        datetime.now(UTC).isoformat(),
                    ),
                )

            for tx in result.accepted_records:
                conn.execute(
                    """
                    INSERT INTO normalized_transactions (
                        transaction_id, batch_id, source_type, source_reference_id,
                        account_id, recipient_id, amount, currency, channel,
                        payment_method, status, timestamp, device_context_json,
                        source_metadata_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tx.transaction_id,
                        batch.batch_id,
                        tx.source_type.value,
                        tx.source_reference_id,
                        tx.account_id,
                        tx.recipient_id,
                        tx.amount,
                        tx.currency,
                        tx.channel.value,
                        tx.payment_method.value,
                        tx.status.value,
                        tx.timestamp.isoformat(),
                        json.dumps(tx.device_context.model_dump()),
                        json.dumps(tx.source_metadata),
                        datetime.now(UTC).isoformat(),
                    ),
                )
    finally:
        if own_conn:
            conn.close()


def get_recent_batches(
    limit: int = 50, conn: sqlite3.Connection | None = None
) -> list[IngestionBatchSummary]:
    """Retrieves recent ingestion batch summaries ordered by creation date."""
    own_conn = False
    if conn is None:
        conn = get_db_connection()
        own_conn = True

    try:
        cursor = conn.execute(
            """
            SELECT batch_id, source_type, filename, total_records,
                   accepted_count, rejected_count, created_at
            FROM ingestion_batches
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        summaries: list[IngestionBatchSummary] = []
        for r in rows:
            summaries.append(
                IngestionBatchSummary(
                    batch_id=r["batch_id"],
                    source_type=SourceType(r["source_type"]),
                    filename=r["filename"],
                    total_records=r["total_records"],
                    accepted_count=r["accepted_count"],
                    rejected_count=r["rejected_count"],
                    created_at=datetime.fromisoformat(r["created_at"]),
                )
            )
        return summaries
    finally:
        if own_conn:
            conn.close()


def get_batch_details(
    batch_id: str, conn: sqlite3.Connection | None = None
) -> IngestionResult | None:
    """Retrieves full details of a batch including errors and accepted transactions."""

    own_conn = False
    if conn is None:
        conn = get_db_connection()
        own_conn = True

    try:
        cursor = conn.execute(
            """
            SELECT batch_id, source_type, filename, total_records,
                   accepted_count, rejected_count, created_at
            FROM ingestion_batches
            WHERE batch_id = ?
            """,
            (batch_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        batch_summary = IngestionBatchSummary(
            batch_id=row["batch_id"],
            source_type=SourceType(row["source_type"]),
            filename=row["filename"],
            total_records=row["total_records"],
            accepted_count=row["accepted_count"],
            rejected_count=row["rejected_count"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

        # Fetch errors
        err_cursor = conn.execute(
            """
            SELECT record_index, reference_id, field, reason, source_type
            FROM validation_errors
            WHERE batch_id = ?
            ORDER BY record_index ASC
            """,
            (batch_id,),
        )
        errors = [
            ValidationErrorItem(
                record_index=r["record_index"],
                reference_id=r["reference_id"],
                field=r["field"],
                reason=r["reason"],
                source_type=SourceType(r["source_type"]),
            )
            for r in err_cursor.fetchall()
        ]

        # Fetch transactions
        tx_cursor = conn.execute(
            """
            SELECT transaction_id, source_type, source_reference_id, account_id,
                   recipient_id, amount, currency, channel, payment_method, status,
                   timestamp, device_context_json, source_metadata_json
            FROM normalized_transactions
            WHERE batch_id = ?
            ORDER BY transaction_id ASC
            """,
            (batch_id,),
        )
        accepted_records = [
            CanonicalTransaction(
                transaction_id=r["transaction_id"],
                source_type=SourceType(r["source_type"]),
                source_reference_id=r["source_reference_id"],
                account_id=r["account_id"],
                recipient_id=r["recipient_id"],
                amount=r["amount"],
                currency=r["currency"],
                channel=ChannelType(r["channel"]),
                payment_method=PaymentMethod(r["payment_method"]),
                status=TransactionStatus(r["status"]),
                timestamp=datetime.fromisoformat(r["timestamp"]),
                device_context=DeviceContext(**json.loads(r["device_context_json"])),
                source_metadata=json.loads(r["source_metadata_json"]),
            )
            for r in tx_cursor.fetchall()
        ]

        return IngestionResult(
            batch=batch_summary,
            accepted_records=accepted_records,
            validation_errors=errors,
        )
    finally:
        if own_conn:
            conn.close()
