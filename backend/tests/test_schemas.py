from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.signals import RiskAssessment, SignalFactor, SignalGroupResult
from app.schemas.transaction import ChannelType, PaymentMethod, Transaction, TransactionStatus


def test_valid_transaction_schema() -> None:
    """Test instantiating a valid Transaction object."""
    tx = Transaction(
        transaction_id="TX-1001",
        account_id="ACC-8821",
        recipient_id="ACC-9904",
        amount=150.50,
        currency="USD",
        channel=ChannelType.MOBILE_APP,
        payment_method=PaymentMethod.DEBIT_CARD,
        status=TransactionStatus.PENDING,
    )

    assert tx.transaction_id == "TX-1001"
    assert tx.amount == 150.50
    assert tx.channel == ChannelType.MOBILE_APP
    assert isinstance(tx.timestamp, datetime)
    assert tx.device_context.is_vpn is False


def test_invalid_transaction_amount() -> None:
    """Test validation error for zero or negative transaction amounts."""
    with pytest.raises(ValidationError):
        Transaction(
            transaction_id="TX-1002",
            account_id="ACC-1",
            recipient_id="ACC-2",
            amount=0.0,
        )


def test_signal_factor_clipping() -> None:
    """Test clipping of factor values outside [0.0, 1.0]."""
    factor_over = SignalFactor(
        name="Urgent Link Click",
        code="PH_LINK_URGENCY",
        raw_value=1.5,
        clipped_value=1.5,
        explanation="High urgency language in phishing email",
    )
    assert factor_over.clipped_value == 1.0

    factor_under = SignalFactor(
        name="Session Anomaly",
        code="AF_SESSION",
        raw_value=-0.3,
        clipped_value=-0.3,
        explanation="Normal session pattern",
    )
    assert factor_under.clipped_value == 0.0


def test_risk_assessment_schema() -> None:
    """Test RiskAssessment composite schema validation."""
    group_af = SignalGroupResult(
        group_code="AF",
        group_name="Adaptive Friction",
        group_weight=0.45,
        raw_score=0.1,
        weighted_score=4.5,
    )

    assessment = RiskAssessment(
        transaction_id="TX-1001",
        risk_score=15.0,
        risk_band="Very Low",
        recommended_action="ALLOW",
        explanation_summary="Transaction displays normal behavior across all signal groups.",
        signal_groups={"AF": group_af},
        str_report_eligible=False,
    )

    assert assessment.risk_score == 15.0
    assert assessment.risk_band == "Very Low"
    assert assessment.recommended_action == "ALLOW"
    assert assessment.str_report_eligible is False
