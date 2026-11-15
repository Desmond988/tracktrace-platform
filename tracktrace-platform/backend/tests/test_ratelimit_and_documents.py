import io

from tests.conftest import auth_headers, make_user


def test_tracking_rate_limit_enforced(client):
    from app.core.config import settings
    limit = int(settings.RATE_LIMIT_TRACKING.split("/")[0])
    for _ in range(limit):
        r = client.get("/api/tracking/NWT-RATE0001")
        assert r.status_code == 404  # not found, but not rate-limited yet
    over = client.get("/api/tracking/NWT-RATE0001")
    assert over.status_code == 429
    assert "retry_after" in over.json()["error"]


def test_login_rate_limit_enforced(client, db):
    from app.core.config import settings
    make_user(db, email="ratelogin@example.com", password="Correct!Passw0rd")
    limit = int(settings.RATE_LIMIT_LOGIN.split("/")[0])
    for _ in range(limit):
        client.post("/api/auth/login", json={"email": "ratelogin@example.com", "password": "Wrong!Passw0rd"})
    over = client.post("/api/auth/login", json={"email": "ratelogin@example.com", "password": "Wrong!Passw0rd"})
    assert over.status_code == 429


def test_document_upload_rejects_bad_content(client, db):
    from sqlalchemy import select
    from app.models import Customer
    u, pw = make_user(db, role="ADMIN")
    headers = auth_headers(client, u.email, pw)
    cust_user, _ = make_user(db, role="CUSTOMER", email="docowner@example.com")
    customer = db.scalar(select(Customer).where(Customer.user_id == cust_user.id))
    sid = client.post("/api/shipments", json={"customer_id": str(customer.id), "origin": "City A", "destination": "City B", "pieces": 1}, headers=headers).json()["id"]

    fake_pdf = io.BytesIO(b"this is not really a pdf")
    r = client.post(f"/api/shipments/{sid}/documents", files={"file": ("doc.pdf", fake_pdf, "application/pdf")}, data={"doc_type": "SHIPPING"}, headers=headers)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "FILE_CONTENT_MISMATCH"


def test_document_visibility_respects_customer_ownership(client, db):
    from sqlalchemy import select
    from app.models import Customer
    u, pw = make_user(db, role="ADMIN")
    headers = auth_headers(client, u.email, pw)
    owner_user, owner_pw = make_user(db, role="CUSTOMER", email="docowner2@example.com")
    other_user, other_pw = make_user(db, role="CUSTOMER", email="docother@example.com")
    customer = db.scalar(select(Customer).where(Customer.user_id == owner_user.id))
    sid = client.post("/api/shipments", json={"customer_id": str(customer.id), "origin": "City A", "destination": "City B", "pieces": 1}, headers=headers).json()["id"]

    real_pdf = io.BytesIO(b"%PDF-1.4\n%fake but has the right header\n")
    up = client.post(f"/api/shipments/{sid}/documents", files={"file": ("proof.pdf", real_pdf, "application/pdf")},
                     data={"doc_type": "PROOF_OF_DELIVERY", "visible_to_customer": "true"}, headers=headers)
    assert up.status_code == 201
    doc_id = up.json()["id"]

    owner_headers = auth_headers(client, owner_user.email, owner_pw)
    other_headers = auth_headers(client, other_user.email, other_pw)

    owner_dl = client.get(f"/api/documents/{doc_id}/download", headers=owner_headers)
    assert owner_dl.status_code == 200
    other_dl = client.get(f"/api/documents/{doc_id}/download", headers=other_headers)
    assert other_dl.status_code == 404
