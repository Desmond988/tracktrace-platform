"""Public quote + contact forms and their staff management."""
import secrets
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user, require_perms
from app.core.errors import err
from app.core.ratelimit import limiter
from app.db.session import get_db
from app.models import ContactMessage, Notification, QuoteRequest, ServiceType, User
from app.schemas.common import Msg, Page
from app.schemas.misc import ContactIn, ContactOut, ContactUpdate, QuoteIn, QuoteOut, QuoteUpdate
from app.services import audit

router = APIRouter(prefix="/api", tags=["quotes & contact"])
REF_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


@router.post("/quotes", status_code=201, dependencies=[Depends(limiter("forms", "RATE_LIMIT_FORMS"))])
def request_quote(body: QuoteIn, request: Request, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    """Public. Stores a quote request. No pricing, payment or checkout is involved."""
    if body.website:  # honeypot tripped: pretend success, store nothing
        return {"reference": "QR-" + "".join(secrets.choice(REF_ALPHABET) for _ in range(8))}
    if body.preferred_service_id and not db.get(ServiceType, body.preferred_service_id):
        raise err(422, "SERVICE_NOT_FOUND", "Choose one of the listed services.")
    data = body.model_dump(exclude={"website"})
    q = QuoteRequest(**data, reference="QR-" + "".join(secrets.choice(REF_ALPHABET) for _ in range(8)),
                     submitted_by_user_id=user.id if user and user.role == "CUSTOMER" else None)
    db.add(q)
    db.flush()
    audit.record(db, "QUOTE_CREATED", user=user, request=request, entity_type="quote", entity_id=q.id, meta={"reference": q.reference})
    db.commit()
    return {"reference": q.reference}


@router.get("/quotes", response_model=Page[QuoteOut])
def list_quotes(status: str | None = None, page: int = 1, page_size: int = 20, user: User = Depends(require_perms("quotes:manage")),
                db: Session = Depends(get_db)):
    page, page_size = max(1, page), min(max(1, page_size), 100)
    conds = [QuoteRequest.status == status] if status else []
    total = db.scalar(select(func.count()).select_from(QuoteRequest).where(*conds)) or 0
    items = db.scalars(select(QuoteRequest).where(*conds).order_by(desc(QuoteRequest.created_at)).limit(page_size).offset((page - 1) * page_size)).all()
    return Page[QuoteOut](items=items, total=total, page=page, page_size=page_size)


@router.patch("/quotes/{quote_id}", response_model=QuoteOut)
def update_quote(quote_id: uuid.UUID, body: QuoteUpdate, request: Request, user: User = Depends(require_perms("quotes:manage")), db: Session = Depends(get_db)):
    q = db.get(QuoteRequest, quote_id)
    if not q:
        raise err(404, "NOT_FOUND", "Quote request not found.")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        if k == "status" and v is None:
            continue
        setattr(q, k, v)
    audit.record(db, "QUOTE_UPDATED", user=user, request=request, entity_type="quote", entity_id=q.id, meta={"fields": sorted(data), "status": q.status})
    db.commit()
    return q


@router.post("/contact", status_code=201, response_model=Msg, dependencies=[Depends(limiter("forms", "RATE_LIMIT_FORMS"))])
def send_contact(body: ContactIn, request: Request, db: Session = Depends(get_db)):
    if body.website:
        return Msg(message="Thank you. We have received your message.")
    m = ContactMessage(**body.model_dump(exclude={"website"}))
    db.add(m)
    db.flush()
    audit.record(db, "CONTACT_MESSAGE_CREATED", request=request, entity_type="contact_message", entity_id=m.id, user_email=body.email)
    db.commit()
    return Msg(message="Thank you. We have received your message.")


@router.get("/messages", response_model=Page[ContactOut])
def list_messages(status: str | None = None, page: int = 1, page_size: int = 20, user: User = Depends(require_perms("messages:manage")),
                  db: Session = Depends(get_db)):
    page, page_size = max(1, page), min(max(1, page_size), 100)
    conds = [ContactMessage.status == status] if status else []
    total = db.scalar(select(func.count()).select_from(ContactMessage).where(*conds)) or 0
    items = db.scalars(select(ContactMessage).where(*conds).order_by(desc(ContactMessage.created_at)).limit(page_size).offset((page - 1) * page_size)).all()
    return Page[ContactOut](items=items, total=total, page=page, page_size=page_size)


@router.patch("/messages/{message_id}", response_model=ContactOut)
def update_message(message_id: uuid.UUID, body: ContactUpdate, request: Request, user: User = Depends(require_perms("messages:manage")), db: Session = Depends(get_db)):
    m = db.get(ContactMessage, message_id)
    if not m:
        raise err(404, "NOT_FOUND", "Message not found.")
    m.status, m.handled_by = body.status, user.id
    audit.record(db, "CONTACT_MESSAGE_UPDATED", user=user, request=request, entity_type="contact_message", entity_id=m.id, meta={"status": m.status})
    db.commit()
    return m


@router.get("/notifications")
def list_notifications(status: str | None = None, channel: str | None = None, page: int = 1, page_size: int = 25,
                       user: User = Depends(require_perms("notifications:read")), db: Session = Depends(get_db)):
    """Delivery log so staff can see exactly what was sent, failed, or skipped because a provider isn't configured."""
    page, page_size = max(1, page), min(max(1, page_size), 100)
    conds = []
    if status:
        conds.append(Notification.status == status)
    if channel:
        conds.append(Notification.channel == channel)
    total = db.scalar(select(func.count()).select_from(Notification).where(*conds)) or 0
    rows = db.scalars(select(Notification).where(*conds).order_by(desc(Notification.created_at)).limit(page_size).offset((page - 1) * page_size)).all()
    items = [{"id": n.id, "shipment_id": n.shipment_id, "channel": n.channel, "template": n.template, "recipient": n.recipient, "subject": n.subject,
              "status": n.status, "error": n.error, "created_at": n.created_at, "sent_at": n.sent_at} for n in rows]
    return {"items": items, "total": total, "page": page, "page_size": page_size}
