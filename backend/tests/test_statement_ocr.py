import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db_connection
from app.main import app
from app.schemas.auth import UserResponse, UserRole
from app.schemas.ingestion import SourceType
from app.services.auth_service import create_token
from app.services.parsers.statement_ocr import StatementOCRParser

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Sets up an isolated test SQLite database for statement OCR tests."""
    db_file = str(tmp_path / "test_statement.db")
    monkeypatch.setattr("app.core.config.settings.database_path", db_file)
    conn = get_db_connection(db_file)
    conn.close()


def get_auth_header(role: str) -> dict[str, str]:
    email = f"{role.lower()}@fraudfusion.io"
    user_resp = UserResponse(
        user_id=f"user-{role.lower()}",
        email=email,
        full_name=f"Test {role}",
        role=UserRole(role),
    )
    token = create_token(user_resp)
    return {"Authorization": f"Bearer {token}"}


def test_statement_ocr_parser_parse_line_high_confidence():
    """Test line parsing with all required fields present produces HIGH confidence."""
    parser = StatementOCRParser()
    line = "2026-09-24 TX-STMT-1001 ACC-SENDER-01 ACC-RECV-02 $1500.00 USD Online Transfer"
    parsed = parser.parse_line(page_num=1, line=line, idx=1, filename="test_statement.pdf")

    assert parsed is not None
    assert parsed.transaction_id == "TX-STMT-1001"
    assert parsed.account_id == "ACC-SENDER-01"
    assert parsed.recipient_id == "ACC-RECV-02"
    assert parsed.amount == 1500.0
    assert parsed.currency == "USD"
    assert parsed.confidence_score == 0.95
    assert parsed.confidence_level == "HIGH"
    assert parsed.is_valid is True


def test_statement_ocr_parser_missing_fields_low_confidence():
    """Test line parsing with missing account IDs flags validation error and LOW confidence."""
    parser = StatementOCRParser()
    line = "2026-09-24 $500.00 USD Miscellaneous Payment"
    parsed = parser.parse_line(page_num=1, line=line, idx=1, filename="statement.txt")

    assert parsed is not None
    assert parsed.amount == 500.0
    assert parsed.is_valid is False
    assert parsed.confidence_level in ("LOW", "NEEDS_REVIEW")
    assert len(parsed.validation_errors) > 0


def test_statement_ocr_parse_statement_summary():
    """Test full statement string parsing into structured extraction result."""
    parser = StatementOCRParser()
    content = (
        b"2026-09-24 TX-STMT-2001 ACC-SENDER-99 ACC-RECV-88 $2500.00 USD Wire Transfer\n"
        b"2026-09-24 TX-STMT-2002 ACC-SENDER-99 ACC-RECV-88 $750.50 USD Mobile Transfer\n"
        b"INVALID LINE WITHOUT AMOUNT OR ACCOUNTS\n"
    )

    res = parser.parse_statement(content, filename="statement.txt")
    assert res.total_lines_scanned >= 3
    assert res.extracted_count == 2
    assert res.valid_count == 2
    assert len(res.extracted_transactions) == 2

    raw_records = parser.convert_to_raw_records(res)
    assert len(raw_records) == 2
    assert raw_records[0]["source_type"] == SourceType.BANK_STATEMENT.value


def test_api_ingest_statement_rbac_enforcement():
    """Test statement ingestion API RBAC enforcement."""
    sample_content = (
        b"2026-09-24 TX-STMT-3001 ACC-SENDER-77 ACC-RECV-66 $3200.00 USD Direct Transfer\n"
    )
    files = {"file": ("statement.txt", sample_content, "text/plain")}

    # Unauthenticated -> 401
    unauth_res = client.post("/api/v1/ingest/statement", files=files)
    assert unauth_res.status_code == 401

    # Viewer -> 403 Forbidden
    viewer_headers = get_auth_header("Viewer")
    viewer_res = client.post("/api/v1/ingest/statement", files=files, headers=viewer_headers)
    assert viewer_res.status_code == 403

    # Analyst -> 201 Created
    analyst_headers = get_auth_header("Analyst")
    analyst_res = client.post("/api/v1/ingest/statement", files=files, headers=analyst_headers)
    assert analyst_res.status_code == 201
    data = analyst_res.json()
    assert data["valid_count"] == 1
    assert data["ingestion_result"]["batch"]["accepted_count"] == 1


def test_normalized_ocr_transactions_investigation_visibility():
    """Test normalized OCR statement transactions are visible in investigation search."""
    sample_content = (
        b"2026-09-24 TX-STMT-4001 ACC-STMT-SENDER ACC-STMT-RECV $9900.00 USD High Risk Wire\n"
    )
    files = {"file": ("statement_high_risk.txt", sample_content, "text/plain")}

    analyst_headers = get_auth_header("Analyst")
    ingest_res = client.post("/api/v1/ingest/statement", files=files, headers=analyst_headers)
    assert ingest_res.status_code == 201

    # Search in investigation API
    search_res = client.get(
        "/api/v1/investigations/transactions?search=TX-STMT-4001",
        headers=analyst_headers,
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total"] >= 1
    assert search_data["items"][0]["transaction_id"] == "TX-STMT-4001"
    assert search_data["items"][0]["amount"] == 9900.0
