"""Password hashing, JWT handling, one-time token helpers."""
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings

_ph = PasswordHasher()  # Argon2id, library defaults
# Verified against when the account doesn't exist so timing doesn't reveal account existence.
_DUMMY_HASH = _ph.hash("timing-equalisation-value")


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        ok = _ph.verify(password_hash or _DUMMY_HASH, password)
    except (VerificationError, InvalidHashError):
        return False
    return bool(ok) and password_hash is not None


def needs_rehash(password_hash: str) -> bool:
    return _ph.check_needs_rehash(password_hash)


def create_access_token(user_id: str, token_version: int) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": user_id, "ver": token_version, "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES), "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM], options={"require": ["exp", "sub"]})
    except jwt.PyJWTError:
        return None


def new_urlsafe_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def validate_password_strength(password: str) -> list[str]:
    """Returns error codes (empty = OK). Length over composition rules (NIST 800-63B)."""
    errors = []
    if len(password) < 10:
        errors.append("PASSWORD_TOO_SHORT")
    if len(password) > 128:
        errors.append("PASSWORD_TOO_LONG")
    if password.lower() in {"password123", "1234567890", "qwertyuiop", "password12", "letmein123"}:
        errors.append("PASSWORD_TOO_COMMON")
    if len(set(password)) < 5:
        errors.append("PASSWORD_TOO_SIMPLE")
    return errors
