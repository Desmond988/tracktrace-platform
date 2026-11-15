"""Multilingual content: statuses/services/FAQ/legal pages return {language: text} dicts with
English fallback, /api/languages lists the supported set, and the staff-only admin endpoints
validate translation payloads. The staff console UI itself stays English-only by design (not tested
here - that's a frontend concern), but the *content* staff manage must support every listed language."""
from tests.conftest import auth_headers, make_user


def test_languages_endpoint_lists_supported_languages(client):
    r = client.get("/api/languages")
    assert r.status_code == 200
    codes = {row["code"] for row in r.json()}
    assert {"en", "fr", "es", "ar", "zh", "sw"} <= codes
    ar = next(row for row in r.json() if row["code"] == "ar")
    assert ar["rtl"] is True
    en = next(row for row in r.json() if row["code"] == "en")
    assert en["rtl"] is False


def test_statuses_return_dict_of_languages_with_english_present(client):
    r = client.get("/api/statuses")
    assert r.status_code == 200
    statuses = r.json()
    assert len(statuses) > 0
    for s in statuses:
        assert "en" in s["label"] and s["label"]["en"]


def test_services_return_dict_of_languages(client):
    r = client.get("/api/services")
    assert r.status_code == 200
    services = r.json()
    assert len(services) > 0
    for s in services:
        assert "en" in s["name"]


def test_faq_returns_multilingual_dicts(client):
    r = client.get("/api/faq")
    assert r.status_code == 200
    items = r.json()
    assert len(items) > 0
    assert "en" in items[0]["question"] and "fr" in items[0]["question"]


def test_public_tracking_service_type_is_localized_dict(client, db):
    from sqlalchemy import select
    from app.models import Customer, ServiceType
    u, pw = make_user(db, role="ADMIN")
    headers = auth_headers(client, u.email, pw)
    cust_user, _ = make_user(db, role="CUSTOMER", email="i18ncust@example.com")
    customer = db.scalar(select(Customer).where(Customer.user_id == cust_user.id))
    svc = db.scalar(select(ServiceType).limit(1))
    r = client.post("/api/shipments", json={"customer_id": str(customer.id), "origin": "City A", "destination": "City B",
                    "pieces": 1, "service_type_id": str(svc.id)}, headers=headers)
    tn = r.json()["tracking_number"]
    pub = client.get(f"/api/tracking/{tn}").json()
    assert pub["service_type"] is not None and "en" in pub["service_type"]


def test_admin_status_create_requires_english_and_validates_language_codes(client, db):
    u, pw = make_user(db, role="SUPER_ADMIN")
    headers = auth_headers(client, u.email, pw)
    missing_en = client.post("/api/admin/statuses", json={"code": "TEST_STATUS_1", "label": {"fr": "Test"}}, headers=headers)
    assert missing_en.status_code == 422
    bad_lang = client.post("/api/admin/statuses", json={"code": "TEST_STATUS_2", "label": {"en": "Test", "xx": "bad"}}, headers=headers)
    assert bad_lang.status_code == 422
    ok = client.post("/api/admin/statuses", json={"code": "TEST_STATUS_3", "label": {"en": "Test Status", "ar": "حالة اختبار"}}, headers=headers)
    assert ok.status_code == 201
    assert ok.json()["label"] == {"en": "Test Status", "ar": "حالة اختبار"}


def test_admin_faq_create_and_legal_update_validate_translations(client, db):
    u, pw = make_user(db, role="SUPER_ADMIN")
    headers = auth_headers(client, u.email, pw)
    faq = client.post("/api/admin/faq", json={"question": {"en": "Test question?"}, "answer": {"en": "Test answer."}}, headers=headers)
    assert faq.status_code == 201

    legal_missing_en = client.put("/api/admin/legal/privacy-policy", json={"title": {"fr": "Titre"}, "body": {"fr": "Corps du texte assez long."}}, headers=headers)
    assert legal_missing_en.status_code == 422

    legal_ok = client.put("/api/admin/legal/privacy-policy", json={
        "title": {"en": "Privacy Policy", "es": "Política de Privacidad"},
        "body": {"en": "This is the updated privacy policy body text.", "es": "Este es el texto actualizado de la política de privacidad."},
        "legally_reviewed": True,
    }, headers=headers)
    assert legal_ok.status_code == 200
    assert legal_ok.json()["title"]["es"] == "Política de Privacidad"
    assert legal_ok.json()["review_note"] is None  # reviewed pages carry no caution note


def test_legal_page_not_yet_reviewed_carries_review_note(client):
    r = client.get("/api/legal/terms-and-conditions")
    assert r.status_code == 200
    assert r.json()["legally_reviewed"] is False
    assert r.json()["review_note"] is not None and "en" in r.json()["review_note"]


def test_settings_locale_languages_accepts_full_supported_set(client, db):
    """Regression: locale.languages validation used to hardcode {"en","fr"}, rejecting any of the
    other 14 supported languages even though the platform fully supports them."""
    u, pw = make_user(db, role="SUPER_ADMIN")
    headers = auth_headers(client, u.email, pw)
    ok = client.put("/api/admin/settings", json={"values": {"locale.languages": ["en", "fr", "ar", "zh", "sw"]}}, headers=headers)
    assert ok.status_code == 200, ok.text
    assert set(ok.json()["values"]["locale.languages"]) == {"en", "fr", "ar", "zh", "sw"}

    bad = client.put("/api/admin/settings", json={"values": {"locale.languages": ["en", "klingon"]}}, headers=headers)
    assert bad.status_code == 422


def test_public_settings_endpoint_exposes_company_fields(client):
    r = client.get("/api/public/settings")
    assert r.status_code == 200
    body = r.json()
    for key in ("company.name", "company.address", "company.phone", "company.email"):
        assert key in body


def test_user_can_be_set_to_any_of_the_16_supported_languages_at_the_database_layer(client, db):
    """Regression: the users.preferred_language CHECK constraint was hardcoded to ('en','fr') and
    never updated when the platform grew to 16 languages, so it silently rejected (500) any of the
    other 14 languages at the database layer even though API-schema validation already accepted
    them. This must be exercised through a real commit, not just schema validation, or it can
    silently regress again."""
    from app.services.i18n import LANGUAGE_CODES
    u, pw = make_user(db, email="alllang@example.com", password="Correct!Passw0rd")
    headers = auth_headers(client, u.email, pw)
    for code in sorted(LANGUAGE_CODES):
        r = client.patch("/api/auth/me", json={"preferred_language": code}, headers=headers)
        assert r.status_code == 200, f"{code} failed: {r.text}"
        assert r.json()["preferred_language"] == code
    db.commit()  # would raise IntegrityError here if the DB constraint were still stale


def test_register_accepts_any_of_the_16_supported_languages(client):
    from app.core import ratelimit
    from app.services.i18n import LANGUAGE_CODES
    ratelimit.ENABLED = False  # this test intentionally registers 16 accounts in a tight loop
    try:
        for code in sorted(LANGUAGE_CODES):
            r = client.post("/api/auth/register", json={
                "name": "Lang Test", "email": f"langtest-{code}@example.com", "phone": "+15550001111",
                "password": "SafeHorse!42", "preferred_language": code,
            })
            assert r.status_code == 201, f"{code} failed: {r.text}"
            assert r.json()["preferred_language"] == code
    finally:
        ratelimit.ENABLED = True
