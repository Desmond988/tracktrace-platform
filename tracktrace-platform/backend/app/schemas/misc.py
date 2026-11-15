import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORM, OptEmail, OptStr, Phone, Str


class CustomerCreate(BaseModel):
    name: Str = Field(min_length=2, max_length=150)
    company: OptStr = Field(default=None, max_length=200)
    email: OptEmail = None
    phone: Phone = None
    notes: OptStr = Field(default=None, max_length=4000)


class CustomerUpdate(BaseModel):
    name: Str | None = Field(default=None, min_length=2, max_length=150)
    company: OptStr = Field(default=None, max_length=200)
    email: OptEmail = None
    phone: Phone = None
    notes: OptStr = Field(default=None, max_length=4000)


class CustomerOut(ORM):
    id: uuid.UUID
    name: str
    company: str | None
    email: str | None
    phone: str | None
    notes: str | None
    user_id: uuid.UUID | None
    created_at: datetime


class LinkUserIn(BaseModel):
    email: EmailStr


class UserCreate(BaseModel):
    name: Str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: Phone = None
    password: str = Field(min_length=1, max_length=200)
    role: str = Field(pattern="^(SUPER_ADMIN|ADMIN|OPERATIONS|STAFF|CUSTOMER)$")


class UserUpdate(BaseModel):
    name: Str | None = Field(default=None, min_length=2, max_length=150)
    phone: Phone = None
    role: str | None = Field(default=None, pattern="^(SUPER_ADMIN|ADMIN|OPERATIONS|STAFF|CUSTOMER)$")
    is_active: bool | None = None
    new_password: str | None = Field(default=None, max_length=200)


class QuoteIn(BaseModel):
    name: Str = Field(min_length=2, max_length=150)
    company: OptStr = Field(default=None, max_length=200)
    email: EmailStr
    phone: Phone = None
    origin: Str = Field(min_length=2, max_length=200)
    destination: Str = Field(min_length=2, max_length=200)
    shipment_type: OptStr = Field(default=None, max_length=80)
    cargo_type: OptStr = Field(default=None, max_length=120)
    weight_kg: float | None = Field(default=None, ge=0, le=1_000_000)
    dimensions: OptStr = Field(default=None, max_length=120)
    pieces: int | None = Field(default=None, ge=1, le=100000)
    preferred_service_id: uuid.UUID | None = None
    additional_info: OptStr = Field(default=None, max_length=4000)
    website: OptStr = Field(default=None, max_length=200)  # honeypot: real users never fill this


class QuoteOut(ORM):
    id: uuid.UUID
    reference: str
    name: str
    company: str | None
    email: str
    phone: str | None
    origin: str
    destination: str
    shipment_type: str | None
    cargo_type: str | None
    weight_kg: float | None
    dimensions: str | None
    pieces: int | None
    preferred_service_id: uuid.UUID | None
    additional_info: str | None
    status: str
    assigned_to: uuid.UUID | None
    internal_notes: str | None
    created_at: datetime
    updated_at: datetime


class QuoteUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(NEW|IN_REVIEW|QUOTED|CLOSED)$")
    assigned_to: uuid.UUID | None = None
    internal_notes: OptStr = Field(default=None, max_length=4000)


class ContactIn(BaseModel):
    name: Str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: Phone = None
    subject: Str = Field(min_length=2, max_length=200)
    message: Str = Field(min_length=5, max_length=5000)
    website: OptStr = Field(default=None, max_length=200)  # honeypot


class ContactOut(ORM):
    id: uuid.UUID
    name: str
    email: str
    phone: str | None
    subject: str
    message: str
    status: str
    created_at: datetime


class ContactUpdate(BaseModel):
    status: str = Field(pattern="^(NEW|READ|REPLIED|ARCHIVED)$")
