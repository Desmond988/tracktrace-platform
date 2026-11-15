from tests.conftest import auth_headers, make_user


def _staff(db, client):
    u, pw = make_user(db, role="ADMIN")
    return auth_headers(client, u.email, pw)


def _customer_with_login(db, client, email):
    u, pw = make_user(db, role="CUSTOMER", email=email)
    from sqlalchemy import select
    from app.models import Customer
    customer = db.scalar(select(Customer).where(Customer.user_id == u.id))
    return u, pw, customer, auth_headers(client, u.email, pw)


def test_create_shipment_generates_unique_tracking_number_and_event(client, db):
    staff = _staff(db, client)
    _, _, customer, _ = _customer_with_login(db, client, "shipowner1@example.com")
    r = client.post("/api/shipments", json={"customer_id": str(customer.id), "origin": "Toronto, CA", "destination": "Vancouver, CA", "pieces": 1}, headers=staff)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["tracking_number"].startswith("NWT-")
    assert len(body["events"]) == 1
    assert body["events"][0]["status"] == "SHIPMENT_CREATED"
    assert body["status"] == "SHIPMENT_CREATED"


def test_tracking_numbers_are_unique_across_many_shipments(client, db):
    staff = _staff(db, client)
    _, _, customer, _ = _customer_with_login(db, client, "shipowner2@example.com")
    numbers = set()
    for _ in range(15):
        r = client.post("/api/shipments", json={"customer_id": str(customer.id), "origin": "City A", "destination": "City B", "pieces": 1}, headers=staff)
        assert r.status_code == 201
        numbers.add(r.json()["tracking_number"])
    assert len(numbers) == 15


def test_public_tracking_returns_real_data_and_hides_customer_details(client, db):
    staff = _staff(db, client)
    _, _, customer, _ = _customer_with_login(db, client, "shipowner3@example.com")
    r = client.post("/api/shipments", json={"customer_id": str(customer.id), "origin": "Origin City", "destination": "Dest City",
                    "sender_name": "Secret Sender", "recipient_email": "recipient@example.com", "pieces": 2}, headers=staff)
    tn = r.json()["tracking_number"]

    pub = client.get(f"/api/tracking/{tn}")
    assert pub.status_code == 200
    data = pub.json()
    assert data["origin"] == "Origin City" and data["destination"] == "Dest City"
    assert "sender_name" not in data and "customer" not in data and "recipient_email" not in data
    assert data["status"]["code"] == "SHIPMENT_CREATED"


def test_public_tracking_invalid_and_not_found(client):
    bad_format = client.get("/api/tracking/not a number!!")
    assert bad_format.status_code == 400
    not_found = client.get("/api/tracking/NWT-ZZZZZZZZ")
    assert not_found.status_code == 404
    assert not_found.json()["error"]["code"] == "TRACKING_NOT_FOUND"


def test_never_fabricates_tracking_data_for_unknown_number(client):
    """Same unknown tracking number queried twice must return the identical 404 - never a fabricated result."""
    r1 = client.get("/api/tracking/NWT-NOTREAL1")
    r2 = client.get("/api/tracking/NWT-NOTREAL1")
    assert r1.status_code == r2.status_code == 404
    assert r1.json() == r2.json()


def test_status_update_creates_new_event_and_preserves_history(client, db):
    staff = _staff(db, client)
    _, _, customer, _ = _customer_with_login(db, client, "shipowner4@example.com")
    sid = client.post("/api/shipments", json={"customer_id": str(customer.id), "origin": "Douala", "destination": "Yaounde", "pieces": 1}, headers=staff).json()["id"]

    r1 = client.post(f"/api/shipments/{sid}/events", json={"status": "IN_TRANSIT", "location": "Douala"}, headers=staff)
    assert r1.status_code == 201
    r2 = client.post(f"/api/shipments/{sid}/events", json={"status": "ARRIVED_AT_FACILITY", "location": "Yaounde"}, headers=staff)
    assert r2.status_code == 201

    events = client.get(f"/api/shipments/{sid}/events", headers=staff).json()
    statuses = [e["status"] for e in events]
    assert statuses == ["SHIPMENT_CREATED", "IN_TRANSIT", "ARRIVED_AT_FACILITY"]  # old events never removed/overwritten

    detail = client.get(f"/api/shipments/{sid}", headers=staff).json()
    assert detail["status"] == "ARRIVED_AT_FACILITY" and detail["current_location"] == "Yaounde"


def test_no_change_event_rejected(client, db):
    staff = _staff(db, client)
    _, _, customer, _ = _customer_with_login(db, client, "shipowner5@example.com")
    sid = client.post("/api/shipments", json={"customer_id": str(customer.id), "origin": "City A", "destination": "City B", "pieces": 1}, headers=staff).json()["id"]
    r = client.post(f"/api/shipments/{sid}/events", json={}, headers=staff)
    assert r.status_code == 422


def test_delivered_is_terminal_and_staff_cannot_reopen(client, db):
    staff = _staff(db, client)
    _, _, customer, _ = _customer_with_login(db, client, "shipowner6@example.com")
    sid = client.post("/api/shipments", json={"customer_id": str(customer.id), "origin": "City A", "destination": "City B", "pieces": 1}, headers=staff).json()["id"]
    client.post(f"/api/shipments/{sid}/events", json={"status": "DELIVERED", "location": "B"}, headers=staff)
    staff_member = _staff2(db, client)
    r = client.post(f"/api/shipments/{sid}/events", json={"status": "IN_TRANSIT"}, headers=staff_member)
    assert r.status_code == 409


def _staff2(db, client):
    u, pw = make_user(db, role="STAFF")
    return auth_headers(client, u.email, pw)


def test_customer_can_only_see_own_shipments(client, db):
    staff = _staff(db, client)
    u1, pw1, cust1, headers1 = _customer_with_login(db, client, "ownera@example.com")
    u2, pw2, cust2, headers2 = _customer_with_login(db, client, "ownerb@example.com")
    sid = client.post("/api/shipments", json={"customer_id": str(cust1.id), "origin": "City A", "destination": "City B", "pieces": 1}, headers=staff).json()["id"]

    mine = client.get(f"/api/me/shipments/{sid}", headers=headers1)
    assert mine.status_code == 200

    other = client.get(f"/api/me/shipments/{sid}", headers=headers2)
    assert other.status_code == 404  # not 403: existence is not confirmed either

    listing = client.get("/api/me/shipments", headers=headers2).json()
    assert listing["total"] == 0


def test_customer_cannot_write_shipments(client, db):
    _, _, cust1, headers1 = _customer_with_login(db, client, "nowrite@example.com")
    r = client.post("/api/shipments", json={"customer_id": str(cust1.id), "origin": "City A", "destination": "City B", "pieces": 1}, headers=headers1)
    assert r.status_code == 403


def test_customer_update_tolerates_empty_email_and_phone(client, db):
    """Regression: CustomerUpdate used to reject an empty-string email with a 422 instead of clearing it."""
    staff = _staff(db, client)
    created = client.post("/api/customers", json={"name": "No Email Yet"}, headers=staff)
    assert created.status_code == 201
    cid = created.json()["id"]
    r = client.patch(f"/api/customers/{cid}", json={"email": "", "phone": ""}, headers=staff)
    assert r.status_code == 200, r.text
    assert r.json()["email"] is None and r.json()["phone"] is None


def test_staff_search_and_filter(client, db):
    staff = _staff(db, client)
    _, _, customer, _ = _customer_with_login(db, client, "searchcust@example.com")
    r = client.post("/api/shipments", json={"customer_id": str(customer.id), "origin": "Search Origin", "destination": "Search Dest", "pieces": 1}, headers=staff)
    tn = r.json()["tracking_number"]
    found = client.get("/api/shipments", params={"q": tn}, headers=staff).json()
    assert found["total"] == 1 and found["items"][0]["tracking_number"] == tn
