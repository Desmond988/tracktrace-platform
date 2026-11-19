import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORM, AwareDT, OptEmail, OptStr, Phone, StatusOut, Str

class AddressIn(BaseModel):
    line1: Str = Field(min_length=1, max_length=255)
    line2: OptStr = Field(default=None, max_length=255)
    city: Str = Field(min_length=1, max_length=100)
    region: OptStr = Field(default=None, max_length=100)
    postal_code: OptStr = Field(default=None, max_length=20)
    country_code: str = Field(pattern="^[A-Za-z]{2}$")

    @field_validator("country_code")
    @classmethod
    def up(cls, v):
        return v.upper()

class AddressOut(ORM):
    line1: str
    line2: str | None
    city: str
    region: str | None
    postal_code: str | None
    country_code: str

class ItemIn(BaseModel):
    description: Str = Field(min_length=1, max_length=300)
    quantity: int = Field(default=1, ge=1, le=100000)
    weight_kg: float | None = Field(default=None, ge=0, le=1_000_000)
    dimensions: OptStr = Field(default=None, max_length=80)
    hs_code: OptStr = Field(default=None, max_length=20)

class ItemOut(ORM):
    id: uuid.UUID
    description: str
    quantity: int
    weight_kg: float | None
    dimensions: str | None
    hs_code: str | None

class _ShipmentBase(BaseModel):
    reference_number: OptStr = Field(default=None, max_length=80)
    service_type_id: uuid.UUID | None = None
    shipment_type: OptStr = Field(default=None, max_length=80)
    sender_name: OptStr = Field(default=None, max_length=150)
    sender_phone: Phone = None
    sender_address: AddressIn | None = None
    recipient_name: OptStr = Field(default=None, max_length=150)
    recipient_phone: Phone = None
    recipient_email: OptEmail = None
    recipient_address: AddressIn | None = None
    weight_kg: float | None = Field(default=None, ge=0, le=1_000_000)
    length_cm: float | None = Field(default=None, ge=0, le=100000)
    width_cm: float | None = Field(default=None, ge=0, le=100000)
    height_cm: float | None = Field(default=None, ge=0, le=100000)
    pieces: int = Field(default=1, ge=1, le=100000)
    cargo_description: OptStr = Field(default=None, max_length=4000)
    special_instructions: OptStr = Field(default=None, max_length=4000)

class ShipmentCreate(_ShipmentBase):
    customer_id: uuid.UUID
    origin: Str = Field(min_length=2, max_length=200)
    destination: Str = Field(min_length=2, max_length=200)
    current_location: OptStr = Field(default=None, max_length=200)
    status: str = Field(default="SHIPMENT_CREATED", max_length=40)
    estimated_delivery: AwareDT = None
    items: list[ItemIn] = Field(default_factory=list, max_length=200)

class ShipmentUpdate(BaseModel):
    """Editable *details*. Status, location and ETA are changed only by adding a tracking event (keeps history intact)."""
    reference_number: OptStr = Field(default=None, max_length=80)
    service_type_id: uuid.UUID | None = None
    shipment_type: OptStr = Field(default=None, max_length=80)
    origin: Str | None = Field(default=None, min_length=2, max_length=200)
    destination: Str | None = Field(default=None, min_length=2, max_length=200)
    sender_name: OptStr = Field(default=None, max_length=150)
    sender_phone: Phone = None
    sender_address: AddressIn | None = None
    recipient_name: OptStr = Field(default=None, max_length=150)
    recipient_phone: Phone = None
    recipient_email: OptEmail = None
    recipient_address: AddressIn | None = None
    weight_kg: float | None = Field(default=None, ge=0, le=1_000_000)
    length_cm: float | None = Field(default=None, ge=0, le=100000)
    width_cm: float | None = Field(default=None, ge=0, le=100000)
    height_cm: float | None = Field(default=None, ge=0, le=100000)
    pieces: int | None = Field(default=None, ge=1, le=100000)
    cargo_description: OptStr = Field(default=None, max_length=4000)
    special_instructions: OptStr = Field(default=None, max_length=4000)
    delivery_notes: OptStr = Field(default=None, max_length=4000)
    received_by: OptStr = Field(default=None, max_length=150)
    items: list[ItemIn] | None = Field(default=None, max_length=200)

class EventCreate(BaseModel):
    status: str | None = Field(default=None, max_length=40)
    location: OptStr = Field(default=None, max_length=200)
    location_id: uuid.UUID | None = None
    description: OptStr = Field(default=None, max_length=2000)
    event_timestamp: AwareDT = None
    estimated_delivery: AwareDT = None
    clear_estimated_delivery: bool = False
    is_public: bool = True
    received_by: OptStr = Field(default=None, max_length=150)

class EventOut(ORM):
    id: uuid.UUID
    status: str
    status_ref: StatusOut | None
    location: str | None
    description: str | None
    event_timestamp: datetime
    is_public: bool
    created_at: datetime
    created_by: uuid.UUID | None = None

class DocumentOut(ORM):
    id: uuid.UUID
    shipment_id: uuid.UUID
    doc_type: str
    filename: str
    content_type: str
    size_bytes: int
    visible_to_customer: bool
    created_at: datetime

class CustomerBrief(ORM):
    id: uuid.UUID
    name: str
    company: str | None
    email: str | None
    phone: str | None

class ShipmentListItem(ORM):
    id: uuid.UUID
    tracking_number: str
    reference_number: str | None
    customer: CustomerBrief
    origin: str
    destination: str
    current_location: str | None
    status: str
    status_ref: StatusOut | None
    estimated_delivery: datetime | None
    actual_delivery: datetime | None
    created_at: datetime
    updated_at: datetime

class ShipmentDetail(ShipmentListItem):
    service_type_id: uuid.UUID | None
    shipment_type: str | None
    sender_name: str | None
    sender_phone: str | None
    sender_address: AddressOut | None
    recipient_name: str | None
    recipient_phone: str | None
    recipient_email: str | None
    recipient_address: AddressOut | None
    weight_kg: float | None
    length_cm: float | None
    width_cm: float | None
    height_cm: float | None
    pieces: int
    cargo_description: str | None
    special_instructions: str | None
    delivery_notes: str | None
    received_by: str | None
    items: list[ItemOut]
    events: list[EventOut]

class PublicEvent(ORM):
    """Public timeline entry: no internal IDs, no staff identity."""
    status: str
    status_ref: StatusOut | None
    location: str | None
    description: str | None
    event_timestamp: datetime

class PublicTracking(BaseModel):
    """Deliberately minimal: no customer, sender/recipient names, addresses, phone numbers or documents."""
    tracking_number: str
    status: StatusOut | None
    origin: str
    destination: str
    current_location: str | None
    created_at: datetime
    estimated_delivery: datetime | None
    actual_delivery: datetime | None
    service_type: dict[str, str] | None
    pieces: int
    updated_at: datetime
    events: list[PublicEvent]