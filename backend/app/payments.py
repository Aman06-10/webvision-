"""Payment state machine.

Application: DRAFT -> PAYMENT_PENDING -> SUBMITTED, or -> PAYMENT_FAILED -> (retry)
Payment:     INITIATED -> PENDING -> PAID | FAILED     (PENDING means "not confirmed yet")
A timeout is never shown as failure; the reconciler asks the gateway instead.
"""
import hashlib
import hmac
import sqlite3
from datetime import datetime

from . import config, db, gateway


class PaymentError(Exception):
    def __init__(self, msg: str, code: int = 400):
        super().__init__(msg)
        self.code = code


def _payment_by_key(c: sqlite3.Connection, key: str):
    return c.execute("SELECT * FROM payments WHERE idem_key=?", (key,)).fetchone()


def _submit(c: sqlite3.Connection, app_id: int) -> None:
    """PAID -> SUBMITTED. The RTI number exists only after confirmed payment."""
    row = c.execute("SELECT rti_number FROM applications WHERE id=?", (app_id,)).fetchone()
    if row["rti_number"]:
        return  # idempotent
    number = f"DEMO/RTI/{datetime.now():%Y}/{app_id:06d}"
    c.execute("UPDATE applications SET state='SUBMITTED', rti_number=?, "
              "updated_at=datetime('now') WHERE id=?", (number, app_id))
    db.log_event(c, app_id, "SUBMITTED", number)


def _resolve(c: sqlite3.Connection, pay, outcome: str, via: str) -> None:
    """Apply a gateway outcome to a payment. Safe to call repeatedly."""
    if pay["status"] in ("PAID", "FAILED"):
        return
    app_id = pay["application_id"]
    if outcome == "success":
        c.execute("UPDATE payments SET status='PAID', updated_at=datetime('now') WHERE id=?",
                  (pay["id"],))
        db.log_event(c, app_id, "PAID", f"via {via}")
        _submit(c, app_id)
    elif outcome == "failed":
        c.execute("UPDATE payments SET status='FAILED', updated_at=datetime('now') WHERE id=?",
                  (pay["id"],))
        c.execute("UPDATE applications SET state='PAYMENT_FAILED', "
                  "updated_at=datetime('now') WHERE id=?", (app_id,))
        db.log_event(c, app_id, "PAYMENT_FAILED", f"via {via}")


def pay(app_id: int, idem_key: str, scenario: str = "success") -> dict:
    with db.tx() as c:
        existing = _payment_by_key(c, idem_key)
        if existing:  # replayed request: same answer, no second charge
            return dict(existing)

        app = c.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
        if not app:
            raise PaymentError("Application not found", 404)
        if not app["authority_confirmed"]:
            raise PaymentError("Confirm the authority before paying")
        if app["state"] not in ("DRAFT", "PAYMENT_FAILED"):
            raise PaymentError(f"Cannot pay while application is {app['state']}", 409)
        if not app["draft"].strip():
            raise PaymentError("Draft is empty")

        try:
            c.execute("INSERT INTO payments(application_id, idem_key, status, amount, scenario) "
                      "VALUES (?,?,?,?,?)",
                      (app_id, idem_key, "INITIATED", config.RTI_FEE_INR, scenario))
        except sqlite3.IntegrityError:
            raise PaymentError("A payment for this application is already in progress", 409)
        db.log_event(c, app_id, "PAYMENT_INITIATED", f"key={idem_key[:8]}")

    # gateway call happens outside the DB transaction
    try:
        outcome = gateway.charge(idem_key, config.RTI_FEE_INR, scenario)
    except gateway.GatewayTimeout:
        outcome = "pending"

    with db.tx() as c:
        pay_row = _payment_by_key(c, idem_key)
        if outcome == "pending":
            c.execute("UPDATE payments SET status='PENDING', updated_at=datetime('now') "
                      "WHERE id=?", (pay_row["id"],))
            c.execute("UPDATE applications SET state='PAYMENT_PENDING', "
                      "updated_at=datetime('now') WHERE id=?", (app_id,))
            db.log_event(c, app_id, "PAYMENT_PENDING", "gateway did not confirm")
        else:
            c.execute("UPDATE applications SET state='PAYMENT_PENDING' WHERE id=?", (app_id,))
            _resolve(c, pay_row, outcome, "direct")
        return dict(_payment_by_key(c, idem_key))


def reconcile() -> int:
    """Resolve every PENDING payment by asking the gateway. Returns how many resolved."""
    resolved = 0
    with db.tx() as c:
        for pay_row in c.execute("SELECT * FROM payments WHERE status='PENDING'").fetchall():
            outcome = gateway.status(pay_row["idem_key"])
            if outcome in ("success", "failed"):
                _resolve(c, pay_row, outcome, "reconciliation")
                resolved += 1
            elif outcome == "unknown":
                db.log_event(c, pay_row["application_id"], "RECONCILE_UNKNOWN",
                             "gateway has no record")
    return resolved


def sign(body: bytes) -> str:
    return hmac.new(config.WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()


def handle_webhook(body: bytes, signature: str, idem_key: str, outcome: str) -> None:
    if not hmac.compare_digest(sign(body), signature):
        raise PaymentError("Bad signature", 401)
    if outcome not in ("success", "failed"):
        raise PaymentError("Bad outcome")
    with db.tx() as c:
        pay_row = _payment_by_key(c, idem_key)
        if not pay_row:
            raise PaymentError("Unknown payment", 404)
        _resolve(c, pay_row, outcome, "webhook")
