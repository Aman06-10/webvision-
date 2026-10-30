import json

import pytest

from app import config, db, gateway, payments
from conftest import make_app, state


def test_success_gives_number():
    a = make_app()
    payments.pay(a, "k1", "success")
    s = state(a)
    assert s["state"] == "SUBMITTED" and s["rti_number"]


def test_replay_same_key_charges_once():
    a = make_app()
    p1 = payments.pay(a, "k1", "success")
    p2 = payments.pay(a, "k1", "success")
    assert p1["id"] == p2["id"]
    with db.tx() as c:
        assert c.execute("SELECT COUNT(*) FROM payments").fetchone()[0] == 1


def test_second_key_while_pending_is_blocked(fresh):
    a = make_app()
    payments.pay(a, "k1", "timeout")
    with pytest.raises(payments.PaymentError) as e:
        payments.pay(a, "k2", "success")
    assert e.value.code == 409


def test_timeout_is_pending_not_failed_then_reconciles(fresh):
    a = make_app()
    payments.pay(a, "k1", "timeout")
    assert state(a)["state"] == "PAYMENT_PENDING" and not state(a)["rti_number"]
    assert payments.reconcile() == 0          # gateway still unsure
    fresh["now"] += gateway.PENDING_RESOLVE_AFTER_S + 1
    assert payments.reconcile() == 1
    s = state(a)
    assert s["state"] == "SUBMITTED" and s["rti_number"]


def test_failure_allows_retry_with_new_key():
    a = make_app()
    payments.pay(a, "k1", "failure")
    assert state(a)["state"] == "PAYMENT_FAILED"
    payments.pay(a, "k2", "success")
    assert state(a)["state"] == "SUBMITTED"


def test_requires_confirmed_authority_and_draft():
    with pytest.raises(payments.PaymentError):
        payments.pay(make_app(authority=False), "k1")
    with pytest.raises(payments.PaymentError):
        payments.pay(make_app(draft="  "), "k2")


def test_webhook_signature_and_idempotency():
    a = make_app()
    payments.pay(a, "k1", "timeout")
    body = json.dumps({"idem_key": "k1", "outcome": "success"}).encode()
    with pytest.raises(payments.PaymentError):
        payments.handle_webhook(body, "bad", "k1", "success")
    sig = payments.sign(body)
    payments.handle_webhook(body, sig, "k1", "success")
    payments.handle_webhook(body, sig, "k1", "success")  # replay is harmless
    assert state(a)["state"] == "SUBMITTED"
    assert payments.reconcile() == 0
