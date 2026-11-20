import hmac
from datetime import UTC, datetime

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.errors import err
from app.core.permissions import has_perm
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User

COOKIE_NAME = "access_token"
CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "x-csrf-token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

def _extract(request: Request) -> tuple[str | None, bool]:
    """Returns (token, from_cookie). Bearer tokens are not ambient credentials so they are exempt from CSRF checks."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip(), False
    tok = request.cookies.get(COOKIE_NAME)
    return (tok, True) if tok else (None, False)

def _load_user(request: Request, db: Session) -> User | None:
    token, from_cookie = _extract(request)
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        raise err(401, "SESSION_EXPIRED", "Your session has expired. Please sign in again.")
    if from_cookie and request.method not in SAFE_METHODS:
        header = (request.headers.get(CSRF_HEADER, "") or "").strip()
        cookie = (request.cookies.get(CSRF_COOKIE, "") or "").strip()
        if not header or not cookie or not hmac.compare_digest(header, cookie):
            raise err(403, "CSRF_FAILED", "Security check failed. Please refresh the page and try again.")
    try:
        user = db.get(User, payload["sub"])
    except Exception:
        user = None
    if (not user or user.deleted_at is not None or not user.is_active or user.token_version != payload.get("ver")):
        raise err(401, "SESSION_EXPIRED", "Your session has expired. Please sign in again.")
    if user.locked_until and user.locked_until > datetime.now(UTC):
        raise err(401, "SESSION_EXPIRED", "Your session has expired. Please sign in again.")
    return user

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = _load_user(request, db)
    if not user:
        raise err(401, "UNAUTHENTICATED", "Please sign in to continue.")
    return user

def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    try:
        return _load_user(request, db)
    except Exception:
        return None

def require_perms(*perms: str):
    def dep(user: User = Depends(get_current_user)) -> User:
        if not all(has_perm(user.role, p) for p in perms):
            raise err(403, "FORBIDDEN", "You do not have permission to do that.")
        return user

    return dep

def require_customer(user: User = Depends(get_current_user)) -> User:
    if user.role != "CUSTOMER":
        raise err(403, "FORBIDDEN", "This area is for customer accounts.")
    return user