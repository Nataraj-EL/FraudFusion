import tempfile

import pytest

from app.core.database import init_db
from app.schemas.ingestion import SourceType
from app.services.ingestion import IngestionService


@pytest.fixture
def temp_db_path() -> str:
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    init_db(tmp.name)
    return tmp.name


def test_ingestion_service_end_to_end(temp_db_path: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.database_path", temp_db_path)

    service = IngestionService()
    csv_content = """transaction_id,sender_account_id,recipient_account_id,amount,currency
TX-ING-01,ACC-A,ACC-B,300.0,USD
TX-ING-02,ACC-C,ACC-D,-50.0,USD
TX-ING-03,ACC-E,ACC-F,1200.0,USD
"""

    result = service.ingest_file(csv_content, "test_ingest.csv", SourceType.FUND_FLOW)

    assert result.batch.total_records == 3
    assert result.batch.accepted_count == 2
    assert result.batch.rejected_count == 1
    assert len(result.accepted_records) == 2
    assert len(result.validation_errors) == 1
    assert result.validation_errors[0].reference_id == "TX-ING-02"

    # Test retrieval from database
    batches = service.list_batches(limit=10)
    assert len(batches) >= 1
    assert batches[0].batch_id == result.batch.batch_id

    fetched_batch = service.get_batch(result.batch.batch_id)
    assert fetched_batch is not None
    assert fetched_batch.batch.accepted_count == 2
    assert fetched_batch.batch.rejected_count == 1
    assert len(fetched_batch.accepted_records) == 2
