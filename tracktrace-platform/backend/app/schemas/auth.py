import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import ORM, Phone, Str
from app.services.i18n import LANGUAGE_CODES


def _valid_language(v: str | None) -> str | None:
    if v is not None and v not in LANGUAGE_CODES:
        raise ValueError(f"Unsupported language. Supported: {', '.join(sorted(LANGUAGE_CODES))}")
    return v


class RegisterIn(BaseModel):
    name: Str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: Phone = Field(...)
    password: str = Field(min_length=1, max_length=200)
    preferred_language: str = Field(default="en")

    _v_lang = field_validator("preferred_language")(_valid_language)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(min_length=1, max_length=200)


class ChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=1, max_length=200)


class ProfileUpdateIn(BaseModel):
    name: Str | None = Field(default=None, min_length=2, max_length=150)
    phone: Phone = None
    preferred_language: str | None = Field(default=None)
    notify_email: bool | None = None
    notify_sms: bool | None = None
    notify_whatsapp: bool | None = None

    _v_lang = field_validator("preferred_language")(_valid_language)


class UserOut(ORM):
    id: uuid.UUID
    name: str
    email: str
    phone: str | None
    role: str
    is_active: bool
    preferred_language: str
    last_login_at: datetime | None = None
    created_at: datetime


class MeOut(UserOut):
    permissions: list[str] = Field(default_factory=list)
    notify_email: bool | None = None
    notify_sms: bool | None = None
    notify_whatsapp: bool | None = None
    customer_id: uuid.UUID | None = None
