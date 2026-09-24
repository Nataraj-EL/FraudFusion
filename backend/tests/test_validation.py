from app.schemas.ingestion import CanonicalTransaction, SourceType
from app.schemas.transaction import ChannelType, PaymentMethod
from app.services.validator import validate_and_normalize_record


def test_validation_valid_af_record() -> None:
    raw = {
        "af_id": "AF-100",
        "account_id": "ACC-10",
        "recipient_id": "ACC-20",
        "amount": 150.0,
        "currency": "USD",
        "channel": "MOBILE_APP",
        "payment_method": "DEBIT_CARD",
        "session_anomaly": 0.75,
        "stepup_failed": True,
    }

    tx, errors = validate_and_normalize_record(raw, 0, SourceType.ADAPTIVE_FRICTION)
    assert len(errors) == 0
    assert tx is not None
    assert isinstance(tx, CanonicalTransaction)
    assert tx.transaction_id == "AF-100"
    assert tx.account_id == "ACC-10"
    assert tx.recipient_id == "ACC-20"
    assert tx.amount == 150.0
    assert tx.channel == ChannelType.MOBILE_APP
    assert tx.payment_method == PaymentMethod.DEBIT_CARD
    assert "af_metrics" in tx.source_metadata
    assert tx.source_metadata["af_metrics"]["session_anomaly"] == 0.75


def test_validation_missing_required_fields() -> None:
    raw = {
        "amount": 50.0,
        "currency": "USD",
    }

    tx, errors = validate_and_normalize_record(raw, 0, SourceType.FUND_FLOW)
    assert tx is None
    assert len(errors) >= 3
    field_names = [e.field for e in errors]
    assert "transaction_id" in field_names
    assert "account_id" in field_names
    assert "recipient_id" in field_names


def test_validation_invalid_amount_types() -> None:
    raw_negative = {
        "tx_id": "TX-NEG",
        "account_id": "ACC-1",
        "recipient_id": "ACC-2",
        "amount": -50.0,
    }

    tx_neg, errors_neg = validate_and_normalize_record(raw_negative, 0, SourceType.FUND_FLOW)
    assert tx_neg is None
    assert len(errors_neg) == 1
    assert errors_neg[0].field == "amount"
    assert "positive" in errors_neg[0].reason

    raw_string_bad = {
        "tx_id": "TX-BAD",
        "account_id": "ACC-1",
        "recipient_id": "ACC-2",
        "amount": "not_a_number",
    }
    tx_bad, errors_bad = validate_and_normalize_record(raw_string_bad, 0, SourceType.FUND_FLOW)
    assert tx_bad is None
    assert len(errors_bad) == 1
    assert errors_bad[0].field == "amount"


def test_mixed_valid_and_invalid_batch_validation() -> None:
    batch = [
        {
            "transaction_id": "TX-V1",
            "account_id": "A1",
            "recipient_id": "R1",
            "amount": 100.0,
        },
        {
            "transaction_id": "TX-INV1",
            "account_id": "A2",
            "recipient_id": "R2",
            "amount": 0.0,  # Invalid zero amount
        },
        {
            "transaction_id": "TX-V2",
            "account_id": "A3",
            "recipient_id": "R3",
            "amount": 250.0,
        },
    ]

    accepted: list[CanonicalTransaction] = []
    rejected_errors: list[list] = []

    for idx, item in enumerate(batch):
        tx, errors = validate_and_normalize_record(item, idx, SourceType.FUND_FLOW)
        if tx:
            accepted.append(tx)
        else:
            rejected_errors.append(errors)

    assert len(accepted) == 2
    assert accepted[0].transaction_id == "TX-V1"
    assert accepted[1].transaction_id == "TX-V2"
    assert len(rejected_errors) == 1
    assert rejected_errors[0][0].reference_id == "TX-INV1"
