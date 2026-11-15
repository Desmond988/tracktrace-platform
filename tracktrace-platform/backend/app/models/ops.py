import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin, uuid_pk


class QuoteRequest(TimestampMixin, Base):
    __tablename__ = "quote_requests"
    __table_args__ = (
        CheckConstraint("status IN ('NEW','IN_REVIEW','QUOTED','CLOSED')", name="ck_quotes_status"),
        Index("ix_quotes_status_created", "status", "created_at"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    reference: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    company: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40))
    origin: Mapped[str] = mapped_column(String(200), nullable=False)
    destination: Mapped[str] = mapped_column(String(200), nullable=False)
    shipment_type: Mapped[str | None] = mapped_column(String(80))
    cargo_type: Mapped[str | None] = mapped_column(String(120))
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    dimensions: Mapped[str | None] = mapped_column(String(120))
    pieces: Mapped[int | None] = mapped_column(Integer)
    preferred_service_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("service_types.id", ondelete="SET NULL"))
    additional_info: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="NEW", server_default="NEW")
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    internal_notes: Mapped[str | None] = mapped_column(Text)
    submitted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))


class ContactMessage(TimestampMixin, Base):
    __tablename__ = "contact_messages"
    __table_args__ = (
        CheckConstraint("status IN ('NEW','READ','REPLIED','ARCHIVED')", name="ck_contact_status"),
        Index("ix_contact_status_created", "status", "created_at"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40))
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="NEW", server_default="NEW")
    handled_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("doc_type IN ('SHIPPING','CUSTOMS','PROOF_OF_DELIVERY','OTHER')", name="ck_documents_type"),
        Index("ix_documents_shipment", "shipment_id"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    shipment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(30), nullable=False, default="OTHER", server_default="OTHER")
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(300), unique=True, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    visible_to_customer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint("channel IN ('EMAIL','SMS','WHATSAPP','IN_APP')", name="ck_notif_channel"),
        CheckConstraint("status IN ('PENDING','SENT','FAILED','SKIPPED_NOT_CONFIGURED')", name="ck_notif_status"),
        Index("ix_notif_user_created", "user_id", "created_at"),
        Index("ix_notif_shipment", "shipment_id"),
        Index("ix_notif_status", "status"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    shipment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"))
    channel: Mapped[str] = mapped_column(String(12), nullable=False)
    template: Mapped[str] = mapped_column(String(60), nullable=False)
    recipient: Mapped[str | None] = mapped_column(String(254))
    subject: Mapped[str | None] = mapped_column(String(250))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING", server_default="PENDING")
    error: Mapped[str | None] = mapped_column(String(500))
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_created", "created_at"),
        Index("ix_audit_action", "action"),
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_user", "user_id"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    user_email: Mapped[str | None] = mapped_column(String(254))
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    meta: Mapped[dict | None] = mapped_column("metadata", JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LegalPage(Base):
    """Editable overrides for legal pages. Defaults (placeholder text needing legal review) live in code.
    `title`/`body` are {language_code: text} dicts - see ShipmentStatus.label for the fallback rule."""
    __tablename__ = "legal_pages"
    slug: Mapped[str] = mapped_column(String(60), primary_key=True)
    title: Mapped[dict] = mapped_column(JSONB, nullable=False)
    body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    legally_reviewed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SiteSetting(Base):
    """Overrides for defaults defined in app/services/site_settings.py."""
    __tablename__ = "site_settings"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict | list | str | int | bool | None] = mapped_column(JSONB)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Faq(Base):
    __tablename__ = "faqs"
    id: Mapped[uuid.UUID] = uuid_pk()
    question: Mapped[dict] = mapped_column(JSONB, nullable=False)
    answer: Mapped[dict] = mapped_column(JSONB, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
