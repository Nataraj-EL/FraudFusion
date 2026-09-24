import base64
import hashlib
import hmac
import json
import os
import sqlite3
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.database import get_db_connection
from app.core.logging import logger
from app.schemas.auth import UserResponse, UserRole


def hash_password(password: str) -> str:
    """Hashes password using PBKDF2-HMAC-SHA256 with 100,000 iterations and random salt."""
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}:{pwd_hash.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against stored salt and PBKDF2 hash string."""
    try:
        salt_hex, hash_hex = hashed_password.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        computed_hash = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt, 100_000
        )
        return hmac.compare_digest(computed_hash, expected_hash)
    except Exception:
        return False


def create_token(user: UserResponse, expires_in_minutes: int = 1440) -> str:
    """Creates a tamper-proof HMAC-SHA256 signed bearer token."""
    expire = datetime.now(UTC) + timedelta(minutes=expires_in_minutes)
    payload = {
        "user_id": user.user_id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "exp": int(expire.timestamp()),
    }
    payload_json = json.dumps(payload, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8")

    sig = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload_b64}.{sig}"


def verify_token(token: str) -> UserResponse | None:
    """Verifies signature and expiration of bearer token and returns UserResponse."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts

        expected_sig = hmac.new(
            settings.jwt_secret_key.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(sig, expected_sig):
            return None

        padding = "=" * (4 - len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8")
        payload = json.loads(payload_json)

        exp = payload.get("exp", 0)
        if datetime.now(UTC).timestamp() > exp:
            return None

        return UserResponse(
            user_id=payload["user_id"],
            email=payload["email"],
            full_name=payload["full_name"],
            role=UserRole(payload["role"]),
        )
    except Exception:
        return None


def seed_default_users(conn: sqlite3.Connection | None = None) -> None:
    """Seeds default development users if users table is empty."""
    own_conn = False
    if conn is None:
        conn = get_db_connection()
        own_conn = True

    try:
        cursor = conn.execute("SELECT COUNT(*) as count FROM users")
        count = cursor.fetchone()["count"]
        if count == 0:
            logger.info("Seeding default FraudFusion RBAC users...")
            default_users = [
                (
                    "USR-ADMIN-01",
                    "admin@fraudfusion.io",
                    "System Admin",
                    "Admin",
                    hash_password("AdminPass123!"),
                ),
                (
                    "USR-ANALYST-01",
                    "analyst@fraudfusion.io",
                    "Lead Fraud Analyst",
                    "Analyst",
                    hash_password("AnalystPass123!"),
                ),
                (
                    "USR-VIEWER-01",
                    "viewer@fraudfusion.io",
                    "Compliance Auditor",
                    "Viewer",
                    hash_password("ViewerPass123!"),
                ),
            ]
            with conn:
                for uid, email, name, role, pwd_hash in default_users:
                    conn.execute(
                        """
                        INSERT INTO users (
                            user_id, email, full_name, role, password_hash, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,

                        (uid, email, name, role, pwd_hash, datetime.now(UTC).isoformat()),
                    )
            logger.info("Default RBAC users seeded successfully.")
    finally:
        if own_conn:
            conn.close()


def authenticate_user(
    email: str, password: str, conn: sqlite3.Connection | None = None
) -> UserResponse | None:
    """Authenticates email and password credentials against SQLite repository."""
    seed_default_users(conn)
    own_conn = False
    if conn is None:
        conn = get_db_connection()
        own_conn = True

    try:
        cursor = conn.execute(
            "SELECT user_id, email, full_name, role, password_hash FROM users WHERE email = ?",
            (email.strip().lower(),),
        )
        user_row = cursor.fetchone()
        if not user_row:
            return None

        if not verify_password(password, user_row["password_hash"]):
            return None

        return UserResponse(
            user_id=user_row["user_id"],
            email=user_row["email"],
            full_name=user_row["full_name"],
            role=UserRole(user_row["role"]),
        )
    finally:
        if own_conn:
            conn.close()


def get_all_users(conn: sqlite3.Connection | None = None) -> list[UserResponse]:
    """Retrieves all registered users for Admin user management."""
    seed_default_users(conn)
    own_conn = False
    if conn is None:
        conn = get_db_connection()
        own_conn = True

    try:
        cursor = conn.execute(
            "SELECT user_id, email, full_name, role, created_at FROM users ORDER BY created_at ASC"
        )
        return [
            UserResponse(
                user_id=row["user_id"],
                email=row["email"],
                full_name=row["full_name"],
                role=UserRole(row["role"]),
                created_at=row["created_at"],
            )
            for row in cursor.fetchall()
        ]
    finally:
        if own_conn:
            conn.close()


def create_user_record(
    email: str,
    full_name: str,
    role: UserRole,
    password: str,
    conn: sqlite3.Connection | None = None,
) -> UserResponse:
    """Creates a new user record in SQLite repository."""
    seed_default_users(conn)
    own_conn = False
    if conn is None:
        conn = get_db_connection()
        own_conn = True

    try:
        user_id = f"USR-{os.urandom(4).hex().upper()}"
        pwd_hash = hash_password(password)
        created_at = datetime.now(UTC).isoformat()

        with conn:
            conn.execute(
                """
                INSERT INTO users (user_id, email, full_name, role, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, email.strip().lower(), full_name, role.value, pwd_hash, created_at),
            )

        return UserResponse(
            user_id=user_id,
            email=email.strip().lower(),
            full_name=full_name,
            role=role,
            created_at=created_at,
        )
    finally:
        if own_conn:
            conn.close()
