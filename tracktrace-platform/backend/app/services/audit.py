from fastapi import Request
from sqlalchemy.orm import Session

from app.core.ratelimit import client_ip
from app.models import AuditLog, User


def record(db: Session, action: str, *, user: User | None = None, request: Request | None = None, entity_type: str | None = None,
           entity_id: object | None = None, meta: dict | None = None, user_email: str | None = None) -> AuditLog:
    """Adds an audit row to the caller's transaction (so it commits/rolls back atomically with the change).
    Never put passwords, tokens or full documents into `meta`."""
    row = AuditLog(
        user_id=user.id if user else None,
        user_email=(user.email if user else user_email),
        action=action, entity_type=entity_type, entity_id=str(entity_id) if entity_id is not None else None,
        meta=meta or None, ip_address=client_ip(request) if request else None,
    )
    db.add(row)
    return row
