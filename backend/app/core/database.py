import sqlite3
from pathlib import Path

from app.core.config import settings


def _ensure_tables_exist(conn: sqlite3.Connection) -> None:
    """Ensures all database schema tables exist on the connection."""
    with conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS ingestion_batches (
                batch_id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                filename TEXT NOT NULL,
                total_records INTEGER NOT NULL,
                accepted_count INTEGER NOT NULL,
                rejected_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS validation_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                record_index INTEGER NOT NULL,
                reference_id TEXT,
                field TEXT NOT NULL,
                reason TEXT NOT NULL,
                source_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (batch_id) REFERENCES ingestion_batches(batch_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS normalized_transactions (
                transaction_id TEXT PRIMARY KEY,
                batch_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_reference_id TEXT NOT NULL,
                account_id TEXT NOT NULL,
                recipient_id TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                channel TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                device_context_json TEXT NOT NULL,
                source_metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (batch_id) REFERENCES ingestion_batches(batch_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS risk_reports (
                transaction_id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                consolidated_score REAL NOT NULL,
                risk_band TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                af_subscore REAL NOT NULL,
                ff_subscore REAL NOT NULL,
                ph_subscore REAL NOT NULL,
                str_status TEXT NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_email TEXT NOT NULL,
                user_role TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                transaction_id TEXT,
                status TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_transactions_batch ON normalized_transactions(batch_id);
            CREATE INDEX IF NOT EXISTS idx_errors_batch ON validation_errors(batch_id);
            CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_email);
            CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
            CREATE INDEX IF NOT EXISTS idx_audit_tx ON audit_logs(transaction_id);

            """
        )


def get_db_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Returns a connected sqlite3.Connection with Row factory enabled."""
    target_path = db_path or settings.database_path
    if target_path != ":memory:":
        path = Path(target_path)
        if not path.is_absolute():
            base_dir = Path(__file__).resolve().parent.parent.parent
            path = base_dir / target_path
        path.parent.mkdir(parents=True, exist_ok=True)
        target_path = str(path)

    conn = sqlite3.connect(target_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _ensure_tables_exist(conn)
    return conn


def init_db(db_path: str | None = None) -> None:
    """Initializes database tables if they do not exist."""
    conn = get_db_connection(db_path)
    conn.close()

