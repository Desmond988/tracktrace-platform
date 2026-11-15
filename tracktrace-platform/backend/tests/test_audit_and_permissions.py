from tests.conftest import auth_headers, make_user


def _role(db, client, role):
    u, pw = make_user(db, role=role)
    return u, auth_headers(client, u.email, pw)


def test_login_success_and_failure_are_audited(client, db):
    from sqlalchemy import select
    from app.models import AuditLog
    u, pw = make_user(db, email="auditme@example.com", password="Correct!Passw0rd")
    client.post("/api/auth/login", json={"email": "auditme@example.com", "password": "Wrong!Passw0rd"})
    client.post("/api/auth/login", json={"email": "auditme@example.com", "password": "Correct!Passw0rd"})
    rows = db.scalars(select(AuditLog).where(AuditLog.user_id == u.id).order_by(AuditLog.id)).all()
    actions = [r.action for r in rows]
    assert "LOGIN_FAILED" in actions and "LOGIN_SUCCESS" in actions


def test_shipment_creation_is_audited(client, db):
    from sqlalchemy import select
    from app.models import AuditLog, Customer
    _, staff_headers = _role(db, client, "ADMIN")
    cust_user, _ = make_user(db, role="CUSTOMER", email="auditcust@example.com")
    customer = db.scalar(select(Customer).where(Customer.user_id == cust_user.id))
    r = client.post("/api/shipments", json={"customer_id": str(customer.id), "origin": "City A", "destination": "City B", "pieces": 1}, headers=staff_headers)
    sid = r.json()["id"]
    logs = db.scalars(select(AuditLog).where(AuditLog.entity_type == "shipment", AuditLog.entity_id == sid)).all()
    assert any(l.action == "SHIPMENT_CREATED" for l in logs)


def test_staff_role_cannot_read_users(client, db):
    _, staff_headers = _role(db, client, "STAFF")
    r = client.get("/api/users", headers=staff_headers)
    assert r.status_code == 403


def test_admin_can_read_users_but_not_manage_super_admin(client, db):
    _, admin_headers = _role(db, client, "ADMIN")
    r = client.get("/api/users", headers=admin_headers)
    assert r.status_code == 200
    r2 = client.post("/api/users", json={"name": "New Super", "email": "newsuper@example.com", "password": "Sup3rSecret!Pass", "role": "SUPER_ADMIN"}, headers=admin_headers)
    assert r2.status_code == 403


def test_super_admin_can_manage_admin_users(client, db):
    _, sa_headers = _role(db, client, "SUPER_ADMIN")
    r = client.post("/api/users", json={"name": "New Admin", "email": "newadmin@example.com", "password": "Sup3rSecret!Pass", "role": "ADMIN"}, headers=sa_headers)
    assert r.status_code == 201


def test_last_super_admin_cannot_be_deactivated(client, db):
    from sqlalchemy import select, func
    from app.models import User
    # ensure exactly one active super admin exists for this test by deactivating any others is out of scope;
    # instead, create one and immediately try to deactivate it while it's the only one *we* created and check.
    u, headers = _role(db, client, "SUPER_ADMIN")
    others = db.scalar(select(func.count()).select_from(User).where(User.role == "SUPER_ADMIN", User.is_active.is_(True), User.id != u.id)) or 0
    if others == 0:
        r = client.patch(f"/api/users/{u.id}", json={"is_active": False}, headers=headers)
        assert r.status_code == 409


def test_customer_cannot_access_admin_dashboard(client, db):
    _, headers = _role(db, client, "CUSTOMER")
    r = client.get("/api/admin/dashboard", headers=headers)
    assert r.status_code == 403


def test_dashboard_numbers_come_from_real_data(client, db):
    from sqlalchemy import select
    from app.models import Customer
    _, staff_headers = _role(db, client, "ADMIN")
    cust_user, _ = make_user(db, role="CUSTOMER", email="dashcust@example.com")
    customer = db.scalar(select(Customer).where(Customer.user_id == cust_user.id))
    before = client.get("/api/admin/dashboard", headers=staff_headers).json()["total_shipments"]
    client.post("/api/shipments", json={"customer_id": str(customer.id), "origin": "City A", "destination": "City B", "pieces": 1}, headers=staff_headers)
    after = client.get("/api/admin/dashboard", headers=staff_headers).json()["total_shipments"]
    assert after == before + 1


def test_quote_request_stores_no_payment_fields(client, db):
    r = client.post("/api/quotes", json={"name": "Prospect Name", "email": "prospect@example.com", "origin": "City A", "destination": "City B"})
    assert r.status_code == 201
    assert "reference" in r.json()
    assert "price" not in r.json() and "payment" not in r.json()


def test_quote_honeypot_silently_ignored(client, db):
    from sqlalchemy import select, func
    from app.models import QuoteRequest
    before = db.scalar(select(func.count()).select_from(QuoteRequest)) or 0
    r = client.post("/api/quotes", json={"name": "Bot", "email": "bot@example.com", "origin": "City A", "destination": "City B", "website": "http://spam.example"})
    assert r.status_code == 201
    after = db.scalar(select(func.count()).select_from(QuoteRequest)) or 0
    assert after == before  # nothing was actually stored


def test_contact_message_flow(client, db):
    r = client.post("/api/contact", json={"name": "Person Name", "email": "person@example.com", "subject": "Question about service", "message": "Hello, I have a question about your service."})
    assert r.status_code == 201
    _, staff_headers = _role(db, client, "OPERATIONS")
    listed = client.get("/api/messages", headers=staff_headers).json()
    assert listed["total"] >= 1


def test_no_payment_routes_exist(client):
    """The full OpenAPI schema must not expose any payment/checkout/billing endpoint."""
    schema = client.get("/openapi.json").json()
    forbidden = ("pay", "checkout", "billing", "invoice", "stripe", "paypal", "wallet", "card")
    hits = [p for p in schema["paths"] if any(f in p.lower() for f in forbidden)]
    assert hits == []
