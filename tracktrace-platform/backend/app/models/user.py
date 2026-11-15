import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, uuid_pk
from app.services.i18n import LANGUAGE_CODES

ROLES = ("SUPER_ADMIN", "ADMIN", "OPERATIONS", "STAFF", "CUSTOMER")
# Built from the single source of truth so the DB constraint can never drift out of sync with
# app.services.i18n.SUPPORTED_LANGUAGES the way it previously did (it was hardcoded to 'en','fr'
# after the platform grew to 16 languages, silently rejecting the other 14 at the database layer
# even though the API schema validation had already been updated).
_LANG_LIST_SQL = ",".join(f"'{c}'" for c in sorted(LANGUAGE_CODES))


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('SUPER_ADMIN','ADMIN','OPERATIONS','STAFF','CUSTOMER')", name="ck_users_role"),
        CheckConstraint(f"preferred_language IN ({_LANG_LIST_SQL})", name="ck_users_language"),
        # Email unique (case-insensitive) among non-deleted users
        Index("uq_users_email_lower_active", text("lower(email)"), unique=True, postgresql_where=text("deleted_at IS NULL")),
        Index("ix_users_role", "role"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="CUSTOMER", server_default="CUSTOMER")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    preferred_language: Mapped[str] = mapped_column(String(5), nullable=False, default="en", server_default="en")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    customer: Mapped["Customer | None"] = relationship(back_populates="user", uselist=False, foreign_keys="Customer.user_id")

    @property
    def is_staff_role(self) -> bool:
        return self.role != "CUSTOMER"


class Customer(TimestampMixin, Base):
    """A customer record. May exist without a login (staff-created) or be linked to a user account."""
    __tablename__ = "customers"
    __table_args__ = (Index("ix_customers_email_lower", text("lower(email)")), Index("ix_customers_name", "name"))
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    company: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(254))
    phone: Mapped[str | None] = mapped_column(String(40))
    notes: Mapped[str | None] = mapped_column(Text)
    notify_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    notify_sms: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    notify_whatsapp: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User | None] = relationship(back_populates="customer", foreign_keys=[user_id])


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (Index("ix_prt_user", "user_id"), Index("ix_prt_expires", "expires_at"))
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    requested_ip: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
