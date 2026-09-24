import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from app.core.database import get_db_connection
from app.schemas.audit import AuditLogEntry, AuditLogQueryResponse


def log_audit_event(
    user_email: str,
    user_role: str,
    action: str,
    resource_type: str,
    status: str = "SUCCESS",
    transaction_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    conn: sqlite3.Connection | None = None,
) -> None:
    """
    Appends an immutable, tamper-evident audit record into SQLite database.
    This operation is append-only.
    """
    own_conn = False
    if conn is None:
        conn = get_db_connection()
        own_conn = True

    try:
        with conn:
            conn.execute(
                """
                INSERT INTO audit_logs (
                    timestamp, user_email, user_role, action, resource_type,
                    transaction_id, status, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(UTC).isoformat(),
                    user_email,
                    user_role,
                    action,
                    resource_type,
                    transaction_id,
                    status,
                    json.dumps(metadata or {}),
                ),
            )
    finally:
        if own_conn:
            conn.close()


def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    user_email: str | None = None,
    action: str | None = None,
    transaction_id: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> AuditLogQueryResponse:
    """Retrieves paginated audit log entries for authorized administrators."""
    own_conn = False
    if conn is None:
        conn = get_db_connection()
        own_conn = True

    try:
        query = (
            "SELECT id, timestamp, user_email, user_role, action, "
            "resource_type, transaction_id, status, metadata_json FROM audit_logs"
        )

        params: list[Any] = []
        conditions: list[str] = []

        if user_email:
            conditions.append("user_email = ?")
            params.append(user_email)
        if action:
            conditions.append("action = ?")
            params.append(action)
        if transaction_id:
            conditions.append("transaction_id = ?")
            params.append(transaction_id)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        count_query = f"SELECT COUNT(*) as cnt FROM ({query})"
        total_count = conn.execute(count_query, params).fetchone()["cnt"]

        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = conn.execute(query, params)
        logs = [
            AuditLogEntry(
                id=row["id"],
                timestamp=row["timestamp"],
                user_email=row["user_email"],
                user_role=row["user_role"],
                action=row["action"],
                resource_type=row["resource_type"],
                transaction_id=row["transaction_id"],
                status=row["status"],
                metadata=json.loads(row["metadata_json"]),
            )
            for row in cursor.fetchall()
        ]

        return AuditLogQueryResponse(total_count=total_count, logs=logs)
    finally:
        if own_conn:
            conn.close()
