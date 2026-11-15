"""Customer self-service area. Ownership is enforced in every query (customer.user_id == current user)."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.deps import require_customer
from app.core.errors import err
from app.db.session import get_db
from app.models import Customer, Document, Notification, QuoteRequest, Shipment, User
from app.schemas.common import Msg, Page
from app.schemas.shipment import DocumentOut, PublicEvent, ShipmentDetail, ShipmentListItem

router = APIRouter(prefix="/api/me", tags=["customer area"])


class MyShipmentDetail(ShipmentDetail):
    events: list[PublicEvent]  # customers never see staff IDs or internal (non-public) events


def _own_shipment(db: Session, user: User, shipment_id: uuid.UUID) -> Shipment:
    s = db.scalar(select(Shipment).join(Customer, Shipment.customer_id == Customer.id)
                  .where(Shipment.id == shipment_id, Shipment.deleted_at.is_(None), Customer.user_id == user.id))
    if not s:
        raise err(404, "SHIPMENT_NOT_FOUND", "Shipment not found.")  # same answer whether it doesn't exist or belongs to someone else
    return s


@router.get("/shipments", response_model=Page[ShipmentListItem])
def my_shipments(page: int = 1, page_size: int = 20, user: User = Depends(require_customer), db: Session = Depends(get_db)):
    page, page_size = max(1, page), min(max(1, page_size), 100)
    conds = [Shipment.deleted_at.is_(None), Customer.user_id == user.id]
    total = db.scalar(select(func.count()).select_from(Shipment).join(Customer, Shipment.customer_id == Customer.id).where(*conds)) or 0
    items = db.scalars(select(Shipment).join(Customer, Shipment.customer_id == Customer.id).where(*conds)
                       .order_by(desc(Shipment.updated_at)).limit(page_size).offset((page - 1) * page_size)).unique().all()
    return Page[ShipmentListItem](items=items, total=total, page=page, page_size=page_size)


@router.get("/shipments/{shipment_id}", response_model=MyShipmentDetail)
def my_shipment(shipment_id: uuid.UUID, user: User = Depends(require_customer), db: Session = Depends(get_db)):
    s = _own_shipment(db, user, shipment_id)
    data = ShipmentDetail.model_validate(s).model_dump(exclude={"events"})
    events = sorted((e for e in s.events if e.is_public), key=lambda e: (e.event_timestamp, e.created_at))
    return MyShipmentDetail(**data, events=[PublicEvent.model_validate(e) for e in events])


@router.get("/shipments/{shipment_id}/documents", response_model=list[DocumentOut])
def my_documents(shipment_id: uuid.UUID, user: User = Depends(require_customer), db: Session = Depends(get_db)):
    s = _own_shipment(db, user, shipment_id)
    return db.scalars(select(Document).where(Document.shipment_id == s.id, Document.deleted_at.is_(None), Document.visible_to_customer.is_(True))
                      .order_by(desc(Document.created_at))).all()


@router.get("/notifications")
def my_notifications(user: User = Depends(require_customer), db: Session = Depends(get_db)):
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id, Notification.channel == "IN_APP")
                      .order_by(desc(Notification.created_at)).limit(100)).all()
    return [{"id": n.id, "shipment_id": n.shipment_id, "subject": n.subject, "body": n.body, "is_read": n.is_read, "created_at": n.created_at} for n in rows]


@router.post("/notifications/{notification_id}/read", response_model=Msg)
def mark_read(notification_id: uuid.UUID, user: User = Depends(require_customer), db: Session = Depends(get_db)):
    n = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id))
    if not n:
        raise err(404, "NOT_FOUND", "Notification not found.")
    n.is_read = True
    db.commit()
    return Msg(message="ok")


@router.get("/quotes")
def my_quotes(user: User = Depends(require_customer), db: Session = Depends(get_db)):
    rows = db.scalars(select(QuoteRequest).where(QuoteRequest.submitted_by_user_id == user.id).order_by(desc(QuoteRequest.created_at))).all()
    return [{"id": q.id, "reference": q.reference, "origin": q.origin, "destination": q.destination, "status": q.status, "created_at": q.created_at} for q in rows]
