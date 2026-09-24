from app.schemas.ingestion import SourceType
from app.services.parsers.af_parser import AdaptiveFrictionParser
from app.services.parsers.factory import auto_detect_source_type, get_parser
from app.services.parsers.ff_parser import FundFlowParser
from app.services.parsers.ph_parser import PhishingParser


def test_af_parser_valid_json() -> None:
    parser = AdaptiveFrictionParser()
    valid_json = """[
        {"transaction_id": "TX-AF-01", "account_id": "ACC-1",
         "recipient_id": "ACC-2", "amount": 100.0, "session_anomaly": 0.8},
        {"transaction_id": "TX-AF-02", "account_id": "ACC-3",
         "recipient_id": "ACC-4", "amount": 250.0, "session_anomaly": 0.1}
    ]"""


    records, errors = parser.parse(valid_json, "test.json")
    assert len(errors) == 0
    assert len(records) == 2
    assert records[0]["transaction_id"] == "TX-AF-01"
    assert records[0]["session_anomaly"] == 0.8


def test_af_parser_malformed_json() -> None:
    parser = AdaptiveFrictionParser()
    malformed_json = "[{'broken_json': true,]"

    records, errors = parser.parse(malformed_json, "bad.json")
    assert len(records) == 0
    assert len(errors) == 1
    assert errors[0].field == "json_syntax"
    assert errors[0].source_type == SourceType.ADAPTIVE_FRICTION


def test_ff_parser_valid_csv() -> None:
    parser = FundFlowParser()
    csv_data = """transaction_id,sender_account_id,recipient_account_id,amount,currency,velocity_24h
TX-FF-01,ACC-101,ACC-202,500.0,USD,5
TX-FF-02,ACC-303,ACC-404,1200.00,USD,12
"""

    records, errors = parser.parse(csv_data, "test.csv")
    assert len(errors) == 0
    assert len(records) == 2
    assert records[0]["transaction_id"] == "TX-FF-01"
    assert records[0]["sender_account_id"] == "ACC-101"
    assert records[0]["velocity_24h"] == "5"


def test_ff_parser_empty_csv() -> None:
    parser = FundFlowParser()
    records, errors = parser.parse("   ", "empty.csv")
    assert len(records) == 0
    assert len(errors) == 1
    assert errors[0].field == "file_empty"


def test_ph_parser_valid_json() -> None:
    parser = PhishingParser()
    valid_json = """{
        "report_id": "PH-991",
        "user_id": "USER-77",
        "phishing_entity_id": "HOST-99",
        "amount": 75.0,
        "domain_similarity": 0.95
    }"""

    records, errors = parser.parse(valid_json, "phish.json")
    assert len(errors) == 0
    assert len(records) == 1
    assert records[0]["report_id"] == "PH-991"
    assert records[0]["domain_similarity"] == 0.95


def test_parser_factory_auto_detect() -> None:
    assert auto_detect_source_type("fund_flow_batch.csv") == SourceType.FUND_FLOW
    assert auto_detect_source_type("phishing_alerts.json") == SourceType.PHISHING
    assert auto_detect_source_type("af_events.json") == SourceType.ADAPTIVE_FRICTION

    af_p = get_parser(SourceType.ADAPTIVE_FRICTION)
    assert isinstance(af_p, AdaptiveFrictionParser)
