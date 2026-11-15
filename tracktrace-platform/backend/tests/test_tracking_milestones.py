"""Milestone statuses added after the carrier capability audit, plus the public-tracking privacy contract.

These run through the real HTTP API and a real PostgreSQL database (no mocks)."""
from sqlalchemy import select

from app.models import AuditLog, Customer, TrackingEvent
from tests.conftest import auth_headers, make_user


def _shipment(client, db, admin_headers, email):
    cust_user, _ = make_user(db, role="CUSTOMER", email=email, phone="+15557770000")
    customer = db.scalar(select(Customer).where(Customer.user_id == cust_user.id))
    r = client.post("/api/shipments", json={
        "customer_id": str(customer.id), "origin": "City A", "destination": "City B", "pieces": 1,
        "sender_name": "Private Sender", "recipient_email": "private-recipient@example.com", "recipient_phone": "+15558889999",
        "special_instructions": "internal gate code 1234",
    }, headers=admin_headers)
    assert r.status_code == 201, r.text
    return r.json()["id"], r.json()["tracking_number"]


def _admin(client, db):
    u, pw = make_user(db, role="ADMIN")
    return auth_headers(client, u.email, pw)


def test_failed_delivery_attempt_is_a_usable_translated_problem_status(client, db):
    admin = _admin(client, db)
    sid, tn = _shipment(client, db, admin, "fda@example.com")
    ev = client.post(f"/api/shipments/{sid}/events", json={"status": "FAILED_DELIVERY_ATTEMPT", "location": "City B", "description": "No one available to receive."}, headers=admin)
    assert ev.status_code == 201
    pub = client.get(f"/api/tracking/{tn}").json()
    assert pub["status"]["code"] == "FAILED_DELIVERY_ATTEMPT"
    assert pub["status"]["is_problem"] is True and pub["status"]["is_terminal"] is False
    assert pub["status"]["label"]["en"] == "Failed Delivery Attempt"
    assert pub["status"]["label"]["ar"] and pub["status"]["label"]["sw"]


def test_public_tracking_exposes_shipment_creation_date(client, db):
    admin = _admin(client, db)
    _, tn = _shipment(client, db, admin, "created@example.com")
    assert client.get(f"/api/tracking/{tn}").json()["created_at"]


def test_staff_role_can_mark_returned_to_sender_and_public_page_shows_it(client, db):
    admin = _admin(client, db)
    sid, tn = _shipment(client, db, admin, "rts@example.com")
    staff_user, staff_pw = make_user(db, role="STAFF")  # lowest staff role, not an admin
    staff = auth_headers(client, staff_user.email, staff_pw)

    client.post(f"/api/shipments/{sid}/events", json={"status": "IN_TRANSIT", "location": "Hub 1"}, headers=staff)
    r = client.post(f"/api/shipments/{sid}/events", json={
        "status": "RETURNED_TO_SENDER", "location": "City A", "description": "Recipient refused delivery; returning to sender."}, headers=staff)
    assert r.status_code == 201, r.text
    assert r.json()["status_ref"]["label"]["en"] == "Returned to Sender"

    pub = client.get(f"/api/tracking/{tn}")  # no credentials at all
    assert pub.status_code == 200
    body = pub.json()
    assert body["status"]["code"] == "RETURNED_TO_SENDER"
    assert body["status"]["is_terminal"] is True and body["status"]["is_problem"] is True
    assert body["status"]["label"]["ar"] == "أُعيدت إلى المرسل"
    assert body["current_location"] == "City A"
    # A returned parcel must never look delivered.
    assert body["actual_delivery"] is None
    # Full append-only history is preserved, in order, ending with the return.
    assert [e["status"] for e in body["events"]] == ["SHIPMENT_CREATED", "IN_TRANSIT", "RETURNED_TO_SENDER"]
    assert body["events"][-1]["description"].startswith("Recipient refused")


def test_returned_to_sender_is_recorded_as_event_and_audited(client, db):
    admin = _admin(client, db)
    sid, _ = _shipment(client, db, admin, "rts-audit@example.com")
    client.post(f"/api/shipments/{sid}/events", json={"status": "RETURNED_TO_SENDER"}, headers=admin)
    events = db.scalars(select(TrackingEvent).where(TrackingEvent.shipment_id == sid)).all()
    assert sorted(e.status for e in events) == ["RETURNED_TO_SENDER", "SHIPMENT_CREATED"]
    actions = {a.action for a in db.scalars(select(AuditLog).where(AuditLog.entity_id == sid))}
    assert {"TRACKING_EVENT_CREATED", "STATUS_CHANGED"} <= actions


def test_returned_to_sender_is_terminal_staff_cannot_reopen_admin_can(client, db):
    admin = _admin(client, db)
    sid, _ = _shipment(client, db, admin, "rts-term@example.com")
    staff_user, staff_pw = make_user(db, role="OPERATIONS")
    ops = auth_headers(client, staff_user.email, staff_pw)
    assert client.post(f"/api/shipments/{sid}/events", json={"status": "RETURNED_TO_SENDER"}, headers=ops).status_code == 201
    assert client.post(f"/api/shipments/{sid}/events", json={"status": "IN_TRANSIT"}, headers=ops).status_code == 409
    assert client.post(f"/api/shipments/{sid}/events", json={"status": "IN_TRANSIT", "description": "Reopened by admin"}, headers=admin).status_code == 201


def test_returned_shipment_is_no_longer_counted_as_active(client, db):
    admin = _admin(client, db)
    sid, _ = _shipment(client, db, admin, "rts-count@example.com")
    before = client.get("/api/admin/dashboard", headers=admin).json()["active_shipments"]
    client.post(f"/api/shipments/{sid}/events", json={"status": "RETURNED_TO_SENDER"}, headers=admin)
    after = client.get("/api/admin/dashboard", headers=admin).json()["active_shipments"]
    assert after == before - 1


def test_only_authorised_staff_can_set_statuses(client, db):
    admin = _admin(client, db)
    sid, tn = _shipment(client, db, admin, "rts-auth@example.com")
    client.cookies.clear()  # the test client keeps a cookie jar; the admin login above would otherwise leak into this "anonymous" call
    assert client.post(f"/api/shipments/{sid}/events", json={"status": "RETURNED_TO_SENDER"}).status_code == 401  # anonymous
    cust_user, cust_pw = make_user(db, role="CUSTOMER")
    cust = auth_headers(client, cust_user.email, cust_pw)
    client.cookies.clear()
    assert client.post(f"/api/shipments/{sid}/events", json={"status": "RETURNED_TO_SENDER"}, headers=cust).status_code == 403
    assert client.get(f"/api/tracking/{tn}").json()["status"]["code"] == "SHIPMENT_CREATED"  # nothing changed


def test_public_tracking_response_contains_only_the_whitelisted_fields(client, db):
    """Privacy contract: knowing a tracking number must not reveal contact details, notes or staff data."""
    admin = _admin(client, db)
    sid, tn = _shipment(client, db, admin, "privacy@example.com")
    client.post(f"/api/shipments/{sid}/events", json={"status": "IN_TRANSIT", "description": "Departed hub"}, headers=admin)
    raw = client.get(f"/api/tracking/{tn}")
    body = raw.json()
    assert set(body) == {"tracking_number", "status", "origin", "destination", "current_location", "created_at", "estimated_delivery",
                         "actual_delivery", "service_type", "pieces", "updated_at", "events"}
    assert set(body["events"][0]) == {"status", "status_ref", "location", "description", "event_timestamp"}  # no created_by / ids
    text = raw.text.lower()
    for secret in ("private-recipient@example.com", "+15558889999", "+15557770000", "private sender", "gate code", "privacy@example.com", "password"):
        assert secret.lower() not in text, f"public tracking leaked: {secret}"


def test_internal_non_public_events_never_appear_publicly(client, db):
    admin = _admin(client, db)
    sid, tn = _shipment(client, db, admin, "internal@example.com")
    client.post(f"/api/shipments/{sid}/events", json={"description": "INTERNAL: customs broker called", "is_public": False}, headers=admin)
    body = client.get(f"/api/tracking/{tn}").json()
    assert all("INTERNAL" not in (e["description"] or "") for e in body["events"])
    assert "INTERNAL" not in str(body)


def test_tracking_works_without_any_account_but_staff_endpoints_do_not(client, db):
    admin = _admin(client, db)
    sid, tn = _shipment(client, db, admin, "noacct@example.com")
    client.cookies.clear()  # genuinely anonymous: drop the admin session the helper created on this shared client
    assert client.get(f"/api/tracking/{tn}").status_code == 200
    for path in ("/api/shipments", f"/api/shipments/{sid}", f"/api/shipments/{sid}/events", "/api/admin/dashboard", "/api/users"):
        assert client.get(path).status_code == 401, path
