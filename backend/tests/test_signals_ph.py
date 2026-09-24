from app.schemas.transaction import Transaction
from app.services.signals.phishing import evaluate_phishing


def test_ph1_domain_age() -> None:
    tx = Transaction(
        transaction_id="TX-PH1-1", account_id="ACC-1", recipient_id="ACC-2", amount=100.0
    )

    # 1. Age 18 days -> 1 - (18/180) = 0.90
    res_18d = evaluate_phishing(tx, custom_metrics={"domain_age_days": 18.0})
    f_18d = res_18d.factors[0]
    assert f_18d.signal_id == "PH1"
    assert f_18d.risk_factor == 0.90
    assert f_18d.triggered is True
    assert "Short domain age" in f_18d.explanation

    # 2. Age 365 days -> 1 - (365/180) = negative -> clipped to 0.00
    res_365d = evaluate_phishing(tx, custom_metrics={"domain_age_days": 365.0})
    f_365d = res_365d.factors[0]
    assert f_365d.risk_factor == 0.00
    assert f_365d.triggered is False


def test_ph2_certificate_quality() -> None:
    tx = Transaction(
        transaction_id="TX-PH2-1", account_id="ACC-1", recipient_id="ACC-2", amount=100.0
    )

    # 1. Self-signed cert -> 1.00
    res_self = evaluate_phishing(tx, custom_metrics={"self_signed": True, "validity_days": 365.0})
    f_self = res_self.factors[1]
    assert f_self.signal_id == "PH2"
    assert f_self.risk_factor == 1.00
    assert f_self.triggered is True
    assert "self-signed" in f_self.explanation

    # 2. Validity < 30 days -> 1.00
    res_short_cert = evaluate_phishing(
        tx, custom_metrics={"self_signed": False, "validity_days": 14.0}
    )
    f_short_cert = res_short_cert.factors[1]
    assert f_short_cert.risk_factor == 1.00
    assert "14 days" in f_short_cert.explanation

    # 3. Standard valid cert -> 0.00
    res_valid_cert = evaluate_phishing(
        tx, custom_metrics={"self_signed": False, "validity_days": 365.0}
    )
    f_valid_cert = res_valid_cert.factors[1]
    assert f_valid_cert.risk_factor == 0.00
    assert f_valid_cert.triggered is False


def test_ph3_blacklist_hit() -> None:
    tx = Transaction(
        transaction_id="TX-PH3-1", account_id="ACC-1", recipient_id="ACC-2", amount=100.0
    )

    # 1. Blacklist hit -> 1.00
    res_hit = evaluate_phishing(tx, custom_metrics={"local_listing": "blacklist"})
    f_hit = res_hit.factors[2]
    assert f_hit.signal_id == "PH3"
    assert f_hit.risk_factor == 1.00
    assert f_hit.triggered is True
    assert "listed on local blacklist" in f_hit.explanation

    # 2. Clean listing -> 0.00
    res_clean = evaluate_phishing(tx, custom_metrics={"local_listing": "clean"})
    f_clean = res_clean.factors[2]
    assert f_clean.risk_factor == 0.00
    assert f_clean.triggered is False
