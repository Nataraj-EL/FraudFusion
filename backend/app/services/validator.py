from datetime import UTC, datetime
from typing import Any

from app.core.logging import logger
from app.schemas.ingestion import CanonicalTransaction, SourceType, ValidationErrorItem
from app.schemas.transaction import ChannelType, DeviceContext, PaymentMethod, TransactionStatus


def _extract_reference_id(raw_record: dict[str, Any]) -> str | None:
    """Helper to extract reference/transaction ID from raw record dictionary."""
    for key in (
        "transaction_id",
        "tx_id",
        "af_id",
        "transfer_id",
        "report_id",
        "phish_id",
        "reference_id",
        "id",
    ):
        if key in raw_record and raw_record[key]:
            return str(raw_record[key])
    return None


def validate_and_normalize_record(
    raw_record: dict[str, Any], record_index: int, source_type: SourceType
) -> tuple[CanonicalTransaction | None, list[ValidationErrorItem]]:
    """
    Validates a raw dictionary record against required field rules for the given source type.
    Rejects invalid records cleanly without silent repair, returning structured validation errors.
    If valid, returns the normalized CanonicalTransaction with preserved source_metadata.
    """
    errors: list[ValidationErrorItem] = []
    ref_id = _extract_reference_id(raw_record)

    # 1. Required Field Checks
    # Map common alternative field names to standard names
    tx_id = (
        raw_record.get("transaction_id")
        or raw_record.get("tx_id")
        or raw_record.get("af_id")
        or raw_record.get("transfer_id")
        or raw_record.get("report_id")
        or raw_record.get("phish_id")
        or raw_record.get("reference_id")
        or raw_record.get("id")
    )

    if not tx_id:
        errors.append(
            ValidationErrorItem(
                record_index=record_index,
                reference_id=ref_id,
                field="transaction_id",
                reason="Missing required transaction/reference identifier",
                source_type=source_type,
            )
        )

    account_id = (
        raw_record.get("account_id")
        or raw_record.get("sender_account_id")
        or raw_record.get("sender_id")
        or raw_record.get("user_id")
        or raw_record.get("target_user_id")
    )
    if not account_id:
        errors.append(
            ValidationErrorItem(
                record_index=record_index,
                reference_id=ref_id,
                field="account_id",
                reason="Missing required sender/user account identifier",
                source_type=source_type,
            )
        )

    recipient_id = (
        raw_record.get("recipient_id")
        or raw_record.get("recipient_account_id")
        or raw_record.get("destination_id")
        or raw_record.get("beneficiary_id")
        or raw_record.get("phishing_entity_id")
    )
    if not recipient_id:
        errors.append(
            ValidationErrorItem(
                record_index=record_index,
                reference_id=ref_id,
                field="recipient_id",
                reason="Missing required recipient/beneficiary identifier",
                source_type=source_type,
            )
        )

    # 2. Amount Type and Range Validation
    amount_raw = raw_record.get("amount")
    amount_val: float | None = None
    if amount_raw is None:
        errors.append(
            ValidationErrorItem(
                record_index=record_index,
                reference_id=ref_id,
                field="amount",
                reason="Missing required numerical amount field",
                source_type=source_type,
            )
        )
    else:
        try:
            amount_val = float(amount_raw)
            if amount_val <= 0.0:
                errors.append(
                    ValidationErrorItem(
                        record_index=record_index,
                        reference_id=ref_id,
                        field="amount",
                        reason=f"Amount must be strictly positive (> 0.0), got {amount_val}",
                        source_type=source_type,
                    )
                )
        except (ValueError, TypeError):
            errors.append(
                ValidationErrorItem(
                    record_index=record_index,
                    reference_id=ref_id,
                    field="amount",
                    reason=f"Invalid numeric value for amount: '{amount_raw}'",
                    source_type=source_type,
                )
            )

    # If critical structural fields failed, reject immediately
    if errors:
        for err in errors:
            logger.warning(
                f"REJECTED RECORD [{source_type.value}] Index {record_index} "
                f"Ref '{ref_id}': {err.field} - {err.reason}"
            )
        return None, errors

    # 3. Enum & Timestamp Parsing
    currency = str(raw_record.get("currency", "USD")).upper()
    if len(currency) != 3:
        errors.append(
            ValidationErrorItem(
                record_index=record_index,
                reference_id=ref_id,
                field="currency",
                reason=f"Currency code must be 3 letters (ISO 4217), got '{currency}'",
                source_type=source_type,
            )
        )

    channel_str = str(raw_record.get("channel", "WEB")).upper()
    try:
        channel_val = ChannelType(channel_str)
    except ValueError:
        errors.append(
            ValidationErrorItem(
                record_index=record_index,
                reference_id=ref_id,
                field="channel",
                reason=f"Invalid channel value: '{channel_str}'",
                source_type=source_type,
            )
        )
        channel_val = ChannelType.WEB

    payment_str = str(raw_record.get("payment_method", "CREDIT_CARD")).upper()
    try:
        payment_val = PaymentMethod(payment_str)
    except ValueError:
        errors.append(
            ValidationErrorItem(
                record_index=record_index,
                reference_id=ref_id,
                field="payment_method",
                reason=f"Invalid payment method: '{payment_str}'",
                source_type=source_type,
            )
        )
        payment_val = PaymentMethod.CREDIT_CARD

    status_str = str(raw_record.get("status", "PENDING")).upper()
    try:
        status_val = TransactionStatus(status_str)
    except ValueError:
        errors.append(
            ValidationErrorItem(
                record_index=record_index,
                reference_id=ref_id,
                field="status",
                reason=f"Invalid transaction status: '{status_str}'",
                source_type=source_type,
            )
        )
        status_val = TransactionStatus.PENDING

    # Parse Timestamp if provided
    ts_raw = raw_record.get("timestamp")
    timestamp_val = datetime.now(UTC)
    if ts_raw:
        if isinstance(ts_raw, datetime):
            timestamp_val = ts_raw
        elif isinstance(ts_raw, int | float):
            timestamp_val = datetime.fromtimestamp(ts_raw, tz=UTC)
        elif isinstance(ts_raw, str):
            try:
                timestamp_val = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except ValueError:
                errors.append(
                    ValidationErrorItem(
                        record_index=record_index,
                        reference_id=ref_id,
                        field="timestamp",
                        reason=f"Invalid ISO timestamp format: '{ts_raw}'",
                        source_type=source_type,
                    )
                )

    if errors:
        for err in errors:
            logger.warning(
                f"REJECTED RECORD [{source_type.value}] Index {record_index} "
                f"Ref '{ref_id}': {err.field} - {err.reason}"
            )
        return None, errors

    # 4. Device Context Extraction
    dev_ctx_raw = raw_record.get("device_context") or {}
    if not isinstance(dev_ctx_raw, dict):
        dev_ctx_raw = {}

    device_context = DeviceContext(
        device_id=str(dev_ctx_raw.get("device_id") or raw_record.get("device_id") or ""),
        ip_address=str(dev_ctx_raw.get("ip_address") or raw_record.get("ip_address") or ""),
        user_agent=dev_ctx_raw.get("user_agent") or raw_record.get("user_agent"),
        is_vpn=bool(dev_ctx_raw.get("is_vpn") or raw_record.get("is_vpn") or False),
        is_tor=bool(dev_ctx_raw.get("is_tor") or raw_record.get("is_tor") or False),
        location_country=dev_ctx_raw.get("location_country") or raw_record.get("location_country"),
    )

    # 5. Extract and Preserve Source Specific Metadata
    source_metadata: dict[str, Any] = {}
    known_std_keys = {
        "transaction_id",
        "tx_id",
        "af_id",
        "transfer_id",
        "report_id",
        "phish_id",
        "reference_id",
        "id",
        "account_id",
        "sender_account_id",
        "sender_id",
        "user_id",
        "target_user_id",
        "recipient_id",
        "recipient_account_id",
        "destination_id",
        "beneficiary_id",
        "phishing_entity_id",
        "amount",
        "currency",
        "channel",
        "payment_method",
        "status",
        "timestamp",
        "device_context",
        "device_id",
        "ip_address",
        "user_agent",
        "is_vpn",
        "is_tor",
        "location_country",
    }


    signal_metrics = {k: v for k, v in raw_record.items() if k not in known_std_keys}
    if source_type == SourceType.ADAPTIVE_FRICTION:
        source_metadata["af_metrics"] = signal_metrics
    elif source_type == SourceType.FUND_FLOW:
        source_metadata["ff_metrics"] = signal_metrics
    elif source_type == SourceType.PHISHING:
        source_metadata["ph_metrics"] = signal_metrics
    elif source_type == SourceType.BANK_STATEMENT:
        source_metadata["statement_metrics"] = signal_metrics


    canonical_tx = CanonicalTransaction(
        transaction_id=str(tx_id),
        source_type=source_type,
        source_reference_id=str(ref_id or tx_id),
        account_id=str(account_id),
        recipient_id=str(recipient_id),
        amount=amount_val,  # type: ignore
        currency=currency,
        channel=channel_val,
        payment_method=payment_val,
        status=status_val,
        timestamp=timestamp_val,
        device_context=device_context,
        source_metadata=source_metadata,
    )

    return canonical_tx, []
