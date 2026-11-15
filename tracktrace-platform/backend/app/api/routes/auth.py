from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import COOKIE_NAME, CSRF_COOKIE, get_current_user
from app.core.config import settings
from app.core.errors import err
from app.core.permissions import ROLE_PERMISSIONS
from app.core.ratelimit import client_ip, limiter
from app.core.security import (
    create_access_token,
    hash_password,
    hash_token,
    needs_rehash,
    new_urlsafe_token,
    validate_password_strength,
    verify_password,
)
from app.db.session import get_db
from app.models import Customer, PasswordResetToken, User
from app.schemas.auth import ChangePasswordIn, ForgotIn, LoginIn, MeOut, ProfileUpdateIn, RegisterIn, ResetIn
from app.schemas.common import Msg
from app.services import audit
from app.services.notifications import send_password_reset_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session(response: Response, user: User) -> str:
    token = create_access_token(str(user.id), user.token_version)
    csrf = new_urlsafe_token()
    common = {"max_age": settings.ACCESS_TOKEN_MINUTES * 60, "secure": settings.COOKIE_SECURE,
              "samesite": settings.COOKIE_SAMESITE, "domain": settings.COOKIE_DOMAIN, "path": "/"}
    response.set_cookie(COOKIE_NAME, token, httponly=True, **common)
    response.set_cookie(CSRF_COOKIE, csrf, httponly=False, **common)  # readable by JS on purpose (double-submit)
    return csrf


def _clear_session(response: Response) -> None:
    for name in (COOKIE_NAME, CSRF_COOKIE):
        response.delete_cookie(name, path="/", domain=settings.COOKIE_DOMAIN)


def me_payload(user: User) -> MeOut:
    out = MeOut.model_validate(user)
    out.permissions = sorted(ROLE_PERMISSIONS.get(user.role, set()))
    c = user.customer
    if c:
        out.notify_email, out.notify_sms, out.notify_whatsapp, out.customer_id = c.notify_email, c.notify_sms, c.notify_whatsapp, c.id
    return out


def _check_password(pw: str):
    problems = validate_password_strength(pw)
    if problems:
        raise err(422, "WEAK_PASSWORD", "Choose a stronger password (at least 10 characters).", reasons=problems)


@router.post("/register", status_code=201, dependencies=[Depends(limiter("register", "RATE_LIMIT_REGISTER"))])
def register(body: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)):
    """Customer self-registration: name, email, phone, password. No verification code is needed to sign in."""
    _check_password(body.password)
    email = body.email.lower()
    exists = db.scalar(select(User.id).where(func.lower(User.email) == email, User.deleted_at.is_(None)))
    if exists:
        raise err(409, "EMAIL_TAKEN", "An account with this email already exists. Try signing in instead.")
    user = User(name=body.name, email=email, phone=body.phone, password_hash=hash_password(body.password), role="CUSTOMER",
                preferred_language=body.preferred_language)
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise err(409, "EMAIL_TAKEN", "An account with this email already exists. Try signing in instead.") from exc
    db.add(Customer(user_id=user.id, name=user.name, email=email, phone=body.phone))
    audit.record(db, "USER_CREATED", user=user, request=request, entity_type="user", entity_id=user.id, meta={"self_registered": True, "role": "CUSTOMER"})
    db.commit()
    db.refresh(user)
    _set_session(response, user)
    return me_payload(user)


@router.post("/login", dependencies=[Depends(limiter("login", "RATE_LIMIT_LOGIN"))])
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    """Email + password only. No OTP, no SMS code, no mandatory 2FA."""
    email = body.email.lower()
    user = db.scalar(select(User).where(func.lower(User.email) == email, User.deleted_at.is_(None)))
    now = datetime.now(UTC)
    locked = bool(user and user.locked_until and user.locked_until > now)
    ok = verify_password(body.password, user.password_hash if user else None)  # always hashes: constant-ish timing
    if not user or not ok or locked or not user.is_active:
        if user and not locked:
            user.failed_login_count += 1
            if user.failed_login_count >= settings.ACCOUNT_LOCK_THRESHOLD:
                user.locked_until = now + timedelta(minutes=settings.ACCOUNT_LOCK_MINUTES)
                user.failed_login_count = 0
        audit.record(db, "LOGIN_FAILED", user=user, request=request, entity_type="user", entity_id=user.id if user else None,
                     user_email=email, meta={"reason": "locked" if locked else "invalid_credentials"})
        db.commit()  # persist the failure even though the request errors out
        raise err(401, "INVALID_CREDENTIALS", "Incorrect email or password, or the account is temporarily locked.")
    user.failed_login_count, user.locked_until, user.last_login_at = 0, None, now
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)
    audit.record(db, "LOGIN_SUCCESS", user=user, request=request, entity_type="user", entity_id=user.id)
    db.commit()
    _set_session(response, user)
    return me_payload(user)


@router.post("/logout", response_model=Msg)
def logout(response: Response):
    _clear_session(response)
    return Msg(message="Signed out.")


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user)):
    return me_payload(user)


@router.patch("/me", response_model=MeOut)
def update_me(body: ProfileUpdateIn, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = body.model_dump(exclude_unset=True)
    for f in ("name", "phone", "preferred_language"):
        if f in data and data[f] is not None:
            setattr(user, f, data[f])
    c = user.customer
    if c:
        for f in ("name", "phone"):
            if f in data and data[f] is not None:
                setattr(c, f, data[f])
        for f in ("notify_email", "notify_sms", "notify_whatsapp"):
            if data.get(f) is not None:
                setattr(c, f, data[f])
    audit.record(db, "USER_UPDATED", user=user, request=request, entity_type="user", entity_id=user.id, meta={"fields": sorted(data), "self": True})
    db.commit()
    return me_payload(user)


@router.post("/forgot-password", status_code=202, response_model=Msg, dependencies=[Depends(limiter("forgot", "RATE_LIMIT_FORGOT"))])
def forgot_password(body: ForgotIn, request: Request, tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Always answers the same way so it can't be used to discover which emails have accounts."""
    generic = Msg(message="If an account exists for that email, we have sent a link to reset the password.")
    email = body.email.lower()
    user = db.scalar(select(User).where(func.lower(User.email) == email, User.deleted_at.is_(None), User.is_active.is_(True)))
    if not user:
        return generic
    db.execute(update(PasswordResetToken).where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
               .values(used_at=datetime.now(UTC)))  # older links stop working
    raw = new_urlsafe_token()
    db.add(PasswordResetToken(user_id=user.id, token_hash=hash_token(raw), requested_ip=client_ip(request),
                              expires_at=datetime.now(UTC) + timedelta(minutes=settings.PASSWORD_RESET_MINUTES)))
    audit.record(db, "PASSWORD_RESET_REQUESTED", user=user, request=request, entity_type="user", entity_id=user.id)
    db.commit()
    link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={raw}"
    tasks.add_task(send_password_reset_email, user.email, link, user.preferred_language)
    return generic


@router.post("/reset-password", response_model=Msg, dependencies=[Depends(limiter("reset", "RATE_LIMIT_FORGOT"))])
def reset_password(body: ResetIn, request: Request, db: Session = Depends(get_db)):
    _check_password(body.new_password)
    tok = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(body.token)).with_for_update())
    now = datetime.now(UTC)
    if not tok or tok.used_at is not None or tok.expires_at < now:
        raise err(400, "INVALID_OR_EXPIRED_TOKEN", "This reset link is invalid or has expired. Please request a new one.")
    user = db.get(User, tok.user_id)
    if not user or user.deleted_at is not None or not user.is_active:
        raise err(400, "INVALID_OR_EXPIRED_TOKEN", "This reset link is invalid or has expired. Please request a new one.")
    tok.used_at = now  # single use
    user.password_hash = hash_password(body.new_password)
    user.token_version += 1  # signs out every existing session
    user.failed_login_count, user.locked_until = 0, None
    audit.record(db, "PASSWORD_RESET_COMPLETED", user=user, request=request, entity_type="user", entity_id=user.id)
    db.commit()
    return Msg(message="Your password has been changed. You can now sign in.")


@router.post("/change-password", response_model=MeOut)
def change_password(body: ChangePasswordIn, request: Request, response: Response, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise err(400, "CURRENT_PASSWORD_INCORRECT", "Your current password is incorrect.")
    _check_password(body.new_password)
    user.password_hash = hash_password(body.new_password)
    user.token_version += 1
    audit.record(db, "PASSWORD_CHANGED", user=user, request=request, entity_type="user", entity_id=user.id)
    db.commit()
    _set_session(response, user)  # keep this device signed in with the new token version
    return me_payload(user)
