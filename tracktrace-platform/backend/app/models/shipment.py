import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, uuid_pk


class ShipmentStatus(Base):
    """Configurable status list. Shipments and events reference `code`.
    `label` is a {language_code: text} dict so any number of languages can be added without a schema
    change; a language missing from the dict falls back to "en" at read time (see app.services.i18n)."""
    __tablename__ = "shipment_statuses"
    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    label: Mapped[dict] = mapped_column(JSONB, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_terminal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    is_problem: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    notify_customer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))


class ServiceType(Base):
    __tablename__ = "service_types"
    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    name: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")


class Location(TimestampMixin, Base):
    """Offices, warehouses, hubs, ports. Suggested when staff add tracking events; optionally shown publicly."""
    __tablename__ = "locations"
    __table_args__ = (CheckConstraint("type IN ('OFFICE','WAREHOUSE','HUB','PORT','AIRPORT','OTHER')", name="ck_locations_type"),)
    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str | None] = mapped_column(String(20), unique=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="OFFICE", server_default="OFFICE")
    address_line: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))
    country_code: Mapped[str | None] = mapped_column(String(2))
    phone: Mapped[str | None] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(254))
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))


class Address(TimestampMixin, Base):
    __tablename__ = "addresses"
    id: Mapped[uuid.UUID] = uuid_pk()
    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)


class Shipment(TimestampMixin, Base):
    __tablename__ = "shipments"
    __table_args__ = (
        CheckConstraint("weight_kg IS NULL OR weight_kg >= 0", name="ck_shipments_weight"),
        CheckConstraint("pieces >= 1", name="ck_shipments_pieces"),
        Index("uq_shipments_tracking_number", "tracking_number", unique=True),
        Index("ix_shipments_customer", "customer_id"),
        Index("ix_shipments_status", "status"),
        Index("ix_shipments_created", "created_at"),
        Index("ix_shipments_reference", "reference_number"),
        Index("ix_shipments_status_updated", "status", "updated_at"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    tracking_number: Mapped[str] = mapped_column(String(40), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(80))
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    service_type_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("service_types.id", ondelete="SET NULL"))
    shipment_type: Mapped[str | None] = mapped_column(String(80))

    sender_name: Mapped[str | None] = mapped_column(String(150))
    sender_phone: Mapped[str | None] = mapped_column(String(40))
    sender_address_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("addresses.id", ondelete="SET NULL"))
    recipient_name: Mapped[str | None] = mapped_column(String(150))
    recipient_phone: Mapped[str | None] = mapped_column(String(40))
    recipient_email: Mapped[str | None] = mapped_column(String(254))
    recipient_address_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("addresses.id", ondelete="SET NULL"))

    origin: Mapped[str] = mapped_column(String(200), nullable=False)
    destination: Mapped[str] = mapped_column(String(200), nullable=False)
    current_location: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(40), ForeignKey("shipment_statuses.code", onupdate="CASCADE"), nullable=False)
    estimated_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    length_cm: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    width_cm: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    pieces: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    cargo_description: Mapped[str | None] = mapped_column(Text)
    special_instructions: Mapped[str | None] = mapped_column(Text)
    delivery_notes: Mapped[str | None] = mapped_column(Text)
    received_by: Mapped[str | None] = mapped_column(String(150))

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    customer = relationship("Customer", lazy="joined")
    service_type = relationship("ServiceType", lazy="joined")
    status_ref = relationship("ShipmentStatus", lazy="joined")
    sender_address = relationship("Address", foreign_keys=[sender_address_id], lazy="joined")
    recipient_address = relationship("Address", foreign_keys=[recipient_address_id], lazy="joined")
    items = relationship("ShipmentItem", cascade="all, delete-orphan", order_by="ShipmentItem.created_at")
    events = relationship("TrackingEvent", cascade="all, delete-orphan", order_by="TrackingEvent.event_timestamp")


class ShipmentItem(Base):
    __tablename__ = "shipment_items"
    __table_args__ = (CheckConstraint("quantity >= 1", name="ck_items_qty"), Index("ix_items_shipment", "shipment_id"))
    id: Mapped[uuid.UUID] = uuid_pk()
    shipment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    dimensions: Mapped[str | None] = mapped_column(String(80))
    hs_code: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TrackingEvent(Base):
    """Append-only history. No API updates or deletes rows here; corrections are new events."""
    __tablename__ = "tracking_events"
    __table_args__ = (Index("ix_events_shipment_time", "shipment_id", "event_timestamp"),)
    id: Mapped[uuid.UUID] = uuid_pk()
    shipment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), ForeignKey("shipment_statuses.code", onupdate="CASCADE"), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200))
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"))
    description: Mapped[str | None] = mapped_column(Text)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    status_ref = relationship("ShipmentStatus", lazy="joined")
