"""Shipment notification dispatch: the three honest outcomes (skipped / sent / failed).

Regression: Notification rows were created without an explicit status, so the 'is it PENDING?' check ran
against None (the DB default is applied only at INSERT) and rows were never handed to the dispatcher at all -
meaning shipment emails would never be sent even with working SMTP credentials."""
from unittest.mock import patch

from sqlalchemy import select

from app.core.config import settings
from app.models import Customer, Notification
from tests.conftest import auth_headers, make_user


def _create_shipment(client, db, customer_email):
    admin, pw = make_user(db, role="ADMIN")
    headers = auth_headers(client, admin.email, pw)
    cust_user, _ = make_user(db, role="CUSTOMER", email=customer_email)
    customer = db.scalar(select(Customer).where(Customer.user_id == cust_user.id))
    r = client.post("/api/shipments", json={"customer_id": str(customer.id), "origin": "City A", "destination": "City B", "pieces": 1}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"], r.json()["tracking_number"], headers


def _email_rows(db, shipment_id):
    db.expire_all()
    return db.scalars(select(Notification).where(Notification.shipment_id == shipment_id, Notification.channel == "EMAIL")).all()


def test_unconfigured_smtp_is_recorded_honestly_as_skipped_never_sent(client, db):
    assert not settings.email_configured
    sid, _, _ = _create_shipment(client, db, "notif-skip@example.com")
    rows = _email_rows(db, sid)
    assert len(rows) == 1
    assert rows[0].status == "SKIPPED_NOT_CONFIGURED"  # resolved by the dispatcher, not left PENDING forever
    assert "SMTP" in (rows[0].error or "")
    assert rows[0].sent_at is None


def test_configured_smtp_actually_sends_and_records_sent(client, db, monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.invalid")
    monkeypatch.setattr(settings, "SMTP_FROM", "noreply@example.com")
    with patch("app.services.notifications._send_email") as send:
        sid, tn, _ = _create_shipment(client, db, "notif-sent@example.com")
        send.assert_called_once()
        to, subject, body = send.call_args[0]
        assert to == "notif-sent@example.com"
        assert tn in subject and f"/track?tn={tn}" in body  # the email carries the real tracking number and link
    rows = _email_rows(db, sid)
    assert [r.status for r in rows] == ["SENT"]
    assert rows[0].sent_at is not None


def test_provider_failure_is_recorded_as_failed_never_as_sent(client, db, monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.invalid")
    monkeypatch.setattr(settings, "SMTP_FROM", "noreply@example.com")
    with patch("app.services.notifications._send_email", side_effect=RuntimeError("connection refused")):
        sid, _, _ = _create_shipment(client, db, "notif-fail@example.com")  # the API request itself must still succeed
    rows = _email_rows(db, sid)
    assert [r.status for r in rows] == ["FAILED"]
    assert rows[0].sent_at is None and rows[0].error == "RuntimeError"


def test_status_change_notifies_in_the_customers_language(client, db, monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.invalid")
    monkeypatch.setattr(settings, "SMTP_FROM", "noreply@example.com")
    sid, _, admin = _create_shipment(client, db, "notif-lang@example.com")
    user = db.scalar(select(Customer).where(Customer.email == "notif-lang@example.com")).user
    client.patch("/api/auth/me", json={"preferred_language": "es"}, headers=auth_headers(client, user.email, "Sup3rSecret!Pass"))
    with patch("app.services.notifications._send_email") as send:
        r = client.post(f"/api/shipments/{sid}/events", json={"status": "RETURNED_TO_SENDER", "location": "City A"}, headers=admin)
        assert r.status_code == 201
        subject = send.call_args[0][1]
        assert "Devuelto al remitente" in subject  # Spanish status label, from the 16-language dictionary
