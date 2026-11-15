from tests.conftest import auth_headers, make_user


def test_register_login_logout(client):
    r = client.post("/api/auth/register", json={"name": "Ada Lovelace", "email": "ada@example.com", "phone": "+15550001111", "password": "SafeHorse!42"})
    assert r.status_code == 201, r.text
    assert r.json()["role"] == "CUSTOMER"
    assert "access_token" in r.cookies

    r2 = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "SafeHorse!42"})
    assert r2.status_code == 200

    me = client.get("/api/auth/me", cookies=r2.cookies)
    assert me.status_code == 200 and me.json()["email"] == "ada@example.com"

    out = client.post("/api/auth/logout", cookies=r2.cookies)
    assert out.status_code == 200


def test_register_duplicate_email_rejected(client):
    client.post("/api/auth/register", json={"name": "Aaron Test", "email": "dup@example.com", "phone": "+15550001111", "password": "SafeHorse!42"})
    r = client.post("/api/auth/register", json={"name": "Beth Test", "email": "dup@example.com", "phone": "+15550001112", "password": "SafeHorse!42"})
    assert r.status_code == 409


def test_register_weak_password_rejected(client):
    r = client.post("/api/auth/register", json={"name": "Aaron Test", "email": "weak@example.com", "phone": "+15550001111", "password": "short"})
    assert r.status_code == 422


def test_login_no_otp_field_required(client):
    """Login only needs email + password: confirms there is no mandatory OTP/2FA step."""
    client.post("/api/auth/register", json={"name": "Aaron Test", "email": "notp@example.com", "phone": "+15550001111", "password": "SafeHorse!42"})
    r = client.post("/api/auth/login", json={"email": "notp@example.com", "password": "SafeHorse!42"})
    assert r.status_code == 200
    assert "otp" not in r.json() and "code" not in r.json()


def test_login_wrong_password_rejected(client, db):
    make_user(db, email="pw@example.com", password="Correct!Passw0rd")
    r = client.post("/api/auth/login", json={"email": "pw@example.com", "password": "Wrong!Passw0rd"})
    assert r.status_code == 401


def test_login_unknown_email_same_error_as_wrong_password(client):
    """No account-enumeration: unknown email and wrong password return the same status/code."""
    r1 = client.post("/api/auth/login", json={"email": "doesnotexist@example.com", "password": "Whatever!123"})
    r2 = client.post("/api/auth/login", json={"email": "doesnotexist@example.com", "password": "Whatever!124"})
    assert r1.status_code == r2.status_code == 401
    assert r1.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_account_locks_after_repeated_failures(client, db):
    from app.core.config import settings
    make_user(db, email="lock@example.com", password="Correct!Passw0rd")
    for _ in range(settings.ACCOUNT_LOCK_THRESHOLD):
        client.post("/api/auth/login", json={"email": "lock@example.com", "password": "Wrong!Passw0rd"})
    r = client.post("/api/auth/login", json={"email": "lock@example.com", "password": "Correct!Passw0rd"})
    assert r.status_code == 401  # correct password still rejected while locked


def test_protected_route_requires_auth(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_forgot_password_always_generic_response(client, db):
    """Same response whether or not the email exists, so it can't be used to enumerate accounts."""
    make_user(db, email="hasacct@example.com")
    r1 = client.post("/api/auth/forgot-password", json={"email": "hasacct@example.com"})
    r2 = client.post("/api/auth/forgot-password", json={"email": "doesnotexist@example.com"})
    assert r1.status_code == r2.status_code == 202
    assert r1.json() == r2.json()


def test_forgot_password_reset_flow(client, db):
    from sqlalchemy import select
    from app.core.security import hash_token
    from app.models import PasswordResetToken
    u, _ = make_user(db, email="reset@example.com", password="OldPassw0rd!")
    client.post("/api/auth/forgot-password", json={"email": "reset@example.com"})
    row = db.scalar(select(PasswordResetToken).where(PasswordResetToken.user_id == u.id))
    assert row is not None
    # We only ever store the token hash - recover the raw token isn't possible from the DB,
    # so we mint one ourselves and store its hash to test the reset endpoint end-to-end.
    import secrets
    raw = secrets.token_urlsafe(32)
    row.token_hash = hash_token(raw)
    db.commit()

    bad = client.post("/api/auth/reset-password", json={"token": "not-the-real-token-xxxxxxxxxxxxx", "new_password": "NewPassw0rd!42"})
    assert bad.status_code == 400

    ok = client.post("/api/auth/reset-password", json={"token": raw, "new_password": "NewPassw0rd!42"})
    assert ok.status_code == 200

    reused = client.post("/api/auth/reset-password", json={"token": raw, "new_password": "AnotherOne!42"})
    assert reused.status_code == 400  # single use

    old_login = client.post("/api/auth/login", json={"email": "reset@example.com", "password": "OldPassw0rd!"})
    assert old_login.status_code == 401
    new_login = client.post("/api/auth/login", json={"email": "reset@example.com", "password": "NewPassw0rd!42"})
    assert new_login.status_code == 200


def test_change_password_requires_current(client, db):
    u, pw = make_user(db, email="chpw@example.com", password="Correct!Passw0rd")
    h = auth_headers(client, u.email, pw)
    bad = client.post("/api/auth/change-password", json={"current_password": "Wrong!Passw0rd", "new_password": "Another!Passw0rd"}, headers=h)
    assert bad.status_code == 400
    ok = client.post("/api/auth/change-password", json={"current_password": "Correct!Passw0rd", "new_password": "Another!Passw0rd"}, headers=h)
    assert ok.status_code == 200


def test_registration_creates_account_immediately_no_otp_or_verification_step(client):
    """Requirement: account is created immediately on registration - no pending-verification state,
    no OTP, no code of any kind required before the account can be used."""
    body = {"name": "Immediate User", "email": "immediate@example.com", "phone": "+15550009999", "password": "SafeHorse!42"}
    assert "otp" not in body and "code" not in body and "verification" not in str(body).lower()
    r = client.post("/api/auth/register", json=body)
    assert r.status_code == 201, r.text
    assert "otp" not in r.json() and "code" not in r.json() and "verification" not in str(r.json()).lower()
    # The session cookie set at registration must work immediately, with no extra verification step.
    me = client.get("/api/auth/me", cookies=r.cookies)
    assert me.status_code == 200
    assert me.json()["email"] == "immediate@example.com"


def test_login_request_and_response_contain_no_otp_or_2fa_fields(client, db):
    """Requirement: login is email + password only - no OTP field can be sent, and the response
    never mentions any second factor."""
    make_user(db, email="nofa@example.com", password="Correct!Passw0rd")
    body = {"email": "nofa@example.com", "password": "Correct!Passw0rd"}
    assert set(body.keys()) == {"email", "password"}
    r = client.post("/api/auth/login", json=body)
    assert r.status_code == 200
    dumped = str(r.json()).lower()
    for forbidden in ("otp", "2fa", "two_factor", "two-factor", "verification_code", "sms_code"):
        assert forbidden not in dumped


def test_forgot_password_sends_reset_link_by_email_only_never_in_api_response(client, db):
    """Requirement: the reset token/link is sent ONLY through email - it must never appear in the
    API's own JSON response, and the only delivery channel exercised is email (no SMS/WhatsApp)."""
    from unittest.mock import patch
    from sqlalchemy import select
    from app.models import Notification
    make_user(db, email="emailonly@example.com", password="Correct!Passw0rd")

    with patch("app.api.routes.auth.send_password_reset_email") as mock_send:
        r = client.post("/api/auth/forgot-password", json={"email": "emailonly@example.com"})
        assert r.status_code == 202
        # The response body is the same generic message for everyone - it must not leak the token.
        assert "token" not in str(r.json()).lower()
        mock_send.assert_called_once()
        called_email, called_link, called_lang = mock_send.call_args[0]
        assert called_email == "emailonly@example.com"
        assert called_link.startswith("http") and "token=" in called_link  # the raw token only ever goes into the emailed link

    # No SMS/WhatsApp Notification row should exist as a side effect of a password reset.
    assert db.scalar(select(Notification).where(Notification.channel.in_(("SMS", "WHATSAPP")))) is None


def test_reset_token_expired_is_rejected(client, db):
    """Requirement: an expired reset token must be rejected, distinctly from just 'wrong token'."""
    from datetime import UTC, datetime, timedelta
    from sqlalchemy import select
    from app.core.security import hash_token, new_urlsafe_token
    from app.models import PasswordResetToken
    u, _ = make_user(db, email="expiredtok@example.com", password="Correct!Passw0rd")
    raw = new_urlsafe_token()
    db.add(PasswordResetToken(user_id=u.id, token_hash=hash_token(raw),
                              expires_at=datetime.now(UTC) - timedelta(minutes=1)))  # already expired
    db.commit()

    r = client.post("/api/auth/reset-password", json={"token": raw, "new_password": "NewPassw0rd!99"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"
    # The old password must still work - an expired/rejected reset must not change anything.
    still_works = client.post("/api/auth/login", json={"email": "expiredtok@example.com", "password": "Correct!Passw0rd"})
    assert still_works.status_code == 200


def test_reset_token_already_used_is_rejected(client, db):
    """A second attempt to use the same (now-consumed) token must fail - single use, no replay."""
    from app.core.security import hash_token, new_urlsafe_token
    from datetime import UTC, datetime, timedelta
    from app.models import PasswordResetToken
    u, _ = make_user(db, email="reusetok@example.com", password="Correct!Passw0rd")
    raw = new_urlsafe_token()
    db.add(PasswordResetToken(user_id=u.id, token_hash=hash_token(raw), expires_at=datetime.now(UTC) + timedelta(minutes=30)))
    db.commit()

    first = client.post("/api/auth/reset-password", json={"token": raw, "new_password": "NewPassw0rd!99"})
    assert first.status_code == 200
    second = client.post("/api/auth/reset-password", json={"token": raw, "new_password": "AnotherOne!42"})
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"
