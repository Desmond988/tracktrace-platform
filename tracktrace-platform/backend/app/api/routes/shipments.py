import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Request, Response, UploadFile
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_perms
from app.core.config import settings
from app.core.errors import err
from app.core.permissions import has_perm
from app.db.session import get_db
from app.models import Address, Customer, Document, Location, Shipment, ShipmentItem, ShipmentStatus, TrackingEvent, User
from app.schemas.common import Page
from app.schemas.shipment import DocumentOut, EventCreate, EventOut, ShipmentCreate, ShipmentDetail, ShipmentListItem, ShipmentUpdate
from app.services import audit, notifications, storage, tracking_number

router = APIRouter(prefix="/api", tags=["shipments"])

SORTABLE = {"created_at": Shipment.created_at, "updated_at": Shipment.updated_at, "tracking_number": Shipment.tracking_number,
            "status": Shipment.status, "estimated_delivery": Shipment.estimated_delivery, "origin": Shipment.origin, "destination": Shipment.destination}

def _like(q: str) -> str:
    return "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"

def _active_status(db: Session, code: str) -> ShipmentStatus:
    st = db.get(ShipmentStatus, code)
    if not st or not st.is_active:
        raise err(422, "INVALID_STATUS", "That status is not available.")
    return st

def _address(db: Session, data) -> Address | None:
    if not data:
        return None
    a = Address(**data.model_dump())
    db.add(a)
    db.flush()
    return a

def _get_shipment(db: Session, shipment_id: uuid.UUID, lock: bool = False) -> Shipment:
    stmt = select(Shipment).where(Shipment.id == shipment_id, Shipment.deleted_at.is_(None))
    if lock:
        stmt = stmt.with_for_update(of=Shipment)
    s = db.execute(stmt).scalar_one_or_none()
    if not s:
        raise err(404, "SHIPMENT_NOT_FOUND", "Shipment not found.")
    return s

@router.get("/shipments", response_model=Page[ShipmentListItem])
def list_shipments(q: str | None = None, status: str | None = None, customer_id: uuid.UUID | None = None, origin: str | None = None,
                   destination: str | None = None, date_from: datetime | None = None, date_to: datetime | None = None,
                   sort: str = "created_at", order: str = "desc", page: int = 1, page_size: int = 20,
                   user: User = Depends(require_perms("shipments:read")), db: Session = Depends(get_db)):
    page, page_size = max(1, page), min(max(1, page_size), 100)
    conds = [Shipment.deleted_at.is_(None)]
    if q:
        p = _like(q.strip())
        conds.append(or_(Shipment.tracking_number.ilike(p, escape="\\"), Shipment.reference_number.ilike(p, escape="\\"),
                         Customer.name.ilike(p, escape="\\"), Customer.email.ilike(p, escape="\\"), Customer.company.ilike(p, escape="\\")))
    if status:
        conds.append(Shipment.status == status)
    if customer_id:
        conds.append(Shipment.customer_id == customer_id)
    if origin:
        conds.append(Shipment.origin.ilike(_like(origin), escape="\\"))
    if destination:
        conds.append(Shipment.destination.ilike(_like(destination), escape="\\"))
    if date_from:
        conds.append(Shipment.created_at >= date_from)
    if date_to:
        conds.append(Shipment.created_at <= date_to)
    col = SORTABLE.get(sort, Shipment.created_at)
    total = db.scalar(select(func.count()).select_from(Shipment).join(Customer, Shipment.customer_id == Customer.id).where(*conds)) or 0
    stmt = (select(Shipment).join(Customer, Shipment.customer_id == Customer.id).where(*conds)
            .order_by(asc(col) if order == "asc" else desc(col), desc(Shipment.id)).limit(page_size).offset((page - 1) * page_size))
    items = db.scalars(stmt).unique().all()
    return Page[ShipmentListItem](items=items, total=total, page=page, page_size=page_size)

@router.post("/shipments", response_model=ShipmentDetail, status_code=201)
def create_shipment(body: ShipmentCreate, request: Request, tasks: BackgroundTasks, user: User = Depends(require_perms("shipments:write")),
                    db: Session = Depends(get_db)):
    customer = db.scalar(select(Customer).where(Customer.id == body.customer_id, Customer.deleted_at.is_(None)))
    if not customer:
        raise err(422, "CUSTOMER_NOT_FOUND", "Choose an existing customer.")
    status = _active_status(db, body.status)
    now = datetime.now(UTC)
    s = Shipment(
        customer_id=customer.id, reference_number=body.reference_number, service_type_id=body.service_type_id, shipment_type=body.shipment_type,
        sender_name=body.sender_name, sender_phone=body.sender_phone, recipient_name=body.recipient_name, recipient_phone=body.recipient_phone,
        recipient_email=body.recipient_email, origin=body.origin, destination=body.destination, current_location=body.current_location or body.origin,
        status=status.code, estimated_delivery=body.estimated_delivery, weight_kg=body.weight_kg, length_cm=body.length_cm, width_cm=body.width_cm,
        height_cm=body.height_cm, pieces=body.pieces, cargo_description=body.cargo_description, special_instructions=body.special_instructions,
        created_by=user.id,
    )
    s.sender_address = _address(db, body.sender_address)
    s.recipient_address = _address(db, body.recipient_address)
    s.items = [ShipmentItem(**i.model_dump()) for i in body.items]
    if status.code == "DELIVERED":
        s.actual_delivery = now
    tracking_number.insert_with_unique_number(db, s)  # 1. unique tracking number + shipment
    event = TrackingEvent(shipment_id=s.id, status=status.code, location=s.current_location, description="Shipment created",
                          event_timestamp=now, created_by=user.id)  # 2. initial tracking event
    db.add(event)
    db.flush()
    audit.record(db, "SHIPMENT_CREATED", user=user, request=request, entity_type="shipment", entity_id=s.id,  # 3. audit
                 meta={"tracking_number": s.tracking_number, "customer_id": str(customer.id), "status": status.code})
    try:
        with db.begin_nested():
            pending = notifications.queue_shipment_notifications(db, s, event)
    except Exception as e:
        print(f"Notification failed but shipment created: {e}")
        pending = []
    db.commit()
    tasks.add_task(notifications.dispatch, [n.id for n in pending])
    return s

@router.get("/shipments/{shipment_id}", response_model=ShipmentDetail)
def get_shipment(shipment_id: uuid.UUID, user: User = Depends(require_perms("shipments:read")), db: Session = Depends(get_db)):
    return _get_shipment(db, shipment_id)

@router.patch("/shipments/{shipment_id}", response_model=ShipmentDetail)
def update_shipment(shipment_id: uuid.UUID, body: ShipmentUpdate, request: Request, user: User = Depends(require_perms("shipments:write")),
                    db: Session = Depends(get_db)):
    """Edits shipment details. Status/location/ETA changes go through POST /events so history is preserved."""
    s = _get_shipment(db, shipment_id, lock=True)
    data = body.model_dump(exclude_unset=True)
    changed = []
    for field in ("sender_address", "recipient_address"):
        if field in data:
            setattr(s, field, _address(db, getattr(body, field)))
            changed.append(field)
            data.pop(field)
    if "items" in data:
        s.items = [ShipmentItem(**i) for i in data.pop("items") or []]
        changed.append("items")
    for k, v in data.items():
        if k in ("origin", "destination", "pieces") and v is None:
            continue
        if getattr(s, k) != v:
            setattr(s, k, v)
            changed.append(k)
    if changed:
        audit.record(db, "SHIPMENT_UPDATED", user=user, request=request, entity_type="shipment", entity_id=s.id,
                     meta={"tracking_number": s.tracking_number, "fields": sorted(changed)})
    db.commit()
    return s

@router.get("/shipments/{shipment_id}/events", response_model=list[EventOut])
def list_events(shipment_id: uuid.UUID, user: User = Depends(require_perms("shipments:read")), db: Session = Depends(get_db)):
    s = _get_shipment(db, shipment_id)
    return sorted(s.events, key=lambda e: (e.event_timestamp, e.created_at))

@router.post("/shipments/{shipment_id}/events", response_model=EventOut, status_code=201)
def add_event(shipment_id: uuid.UUID, body: EventCreate, request: Request, tasks: BackgroundTasks,
              user: User = Depends(require_perms("events:write")), db: Session = Depends(get_db)):
    """Adds a NEW tracking event and updates the shipment's current state. Old events are never modified or deleted."""
    s = _get_shipment(db, shipment_id, lock=True)  # row lock: concurrent updates are serialised
    now = datetime.now(UTC)
    ts = body.event_timestamp or now
    if ts > now + timedelta(minutes=5):
        raise err(422, "EVENT_IN_FUTURE", "The event time cannot be in the future.")

    new_status = body.status or s.status
    status = _active_status(db, new_status)
    status_changed = new_status != s.status
    if status_changed and s.status_ref.is_terminal and user.role not in ("ADMIN", "SUPER_ADMIN"):
        raise err(409, "SHIPMENT_CLOSED", "This shipment is already closed. An administrator must reopen it.")

    location = body.location
    if body.location_id:
        loc = db.get(Location, body.location_id)
        if not loc:
            raise err(422, "LOCATION_NOT_FOUND", "That location does not exist.")
        location = location or ", ".join(x for x in (loc.name, loc.city) if x)
    location_changed = location is not None and location != s.current_location
    eta_changed = (body.estimated_delivery is not None and body.estimated_delivery != s.estimated_delivery) or (
        body.clear_estimated_delivery and s.estimated_delivery is not None)
    if not (status_changed or location_changed or eta_changed or body.description):
        raise err(422, "NO_CHANGE", "Nothing to record. Change the status, location or estimated delivery, or add a note.")

    latest_ts = db.scalar(select(func.max(TrackingEvent.event_timestamp)).where(TrackingEvent.shipment_id == s.id))
    is_latest = latest_ts is None or ts >= latest_ts  # a backdated correction must not overwrite the current state

    description = body.description
    if not description and eta_changed and not (status_changed or location_changed):
        description = "Estimated delivery updated"
    event = TrackingEvent(shipment_id=s.id, status=status.code, location=location if location is not None else s.current_location,
                          location_id=body.location_id, description=description, event_timestamp=ts, is_public=body.is_public, created_by=user.id)
    db.add(event)
    old = {"status": s.status, "location": s.current_location, "eta": s.estimated_delivery.isoformat() if s.estimated_delivery else None}
    if is_latest:
        s.status = status.code
        if location is not None:
            s.current_location = location
        if body.clear_estimated_delivery:
            s.estimated_delivery = None
        elif body.estimated_delivery is not None:
            s.estimated_delivery = body.estimated_delivery
        if status.code == "DELIVERED":
            s.actual_delivery = ts
            if body.received_by:
                s.received_by = body.received_by
        elif status_changed:
            s.actual_delivery = None
    db.flush()
    base = {"tracking_number": s.tracking_number, "backdated": not is_latest}
    audit.record(db, "TRACKING_EVENT_CREATED", user=user, request=request, entity_type="shipment", entity_id=s.id, meta={**base, "event_id": str(event.id)})
    if status_changed:
        audit.record(db, "STATUS_CHANGED", user=user, request=request, entity_type="shipment", entity_id=s.id, meta={**base, "from": old["status"], "to": status.code})
    if location_changed:
        audit.record(db, "LOCATION_CHANGED", user=user, request=request, entity_type="shipment", entity_id=s.id, meta={**base, "from": old["location"], "to": location})
    if eta_changed:
        audit.record(db, "SHIPMENT_UPDATED", user=user, request=request, entity_type="shipment", entity_id=s.id, meta={**base, "fields": ["estimated_delivery"], "from": old["eta"]})
    if status.code == "DELIVERED" and status_changed:
        audit.record(db, "DELIVERY_CONFIRMED", user=user, request=request, entity_type="shipment", entity_id=s.id, meta=base)
    pending = []
    if status_changed and is_latest:
        try:
            with db.begin_nested():
                pending = notifications.queue_shipment_notifications(db, s, event)
        except Exception as e:
            print(f"Notification failed but event saved: {e}")
            pending = []
    db.commit()
    tasks.add_task(notifications.dispatch, [n.id for n in pending])
    return event

# ---------------- documents ----------------
@router.get("/shipments/{shipment_id}/documents", response_model=list[DocumentOut])
def list_documents(shipment_id: uuid.UUID, user: User = Depends(require_perms("shipments:read")), db: Session = Depends(get_db)):
    _get_shipment(db, shipment_id)
    return db.scalars(select(Document).where(Document.shipment_id == shipment_id, Document.deleted_at.is_(None)).order_by(Document.created_at.desc())).all()

@router.post("/shipments/{shipment_id}/documents", response_model=DocumentOut, status_code=201)
def upload_document(shipment_id: uuid.UUID, request: Request, file: UploadFile = File(...), doc_type: str = Form("OTHER"),
                    visible_to_customer: bool = Form(False), user: User = Depends(require_perms("documents:write")), db: Session = Depends(get_db)):
    s = _get_shipment(db, shipment_id)
    if doc_type not in ("SHIPPING", "CUSTOMS", "PROOF_OF_DELIVERY", "OTHER"):
        raise err(422, "INVALID_DOCUMENT_TYPE", "Unknown document type.")
    data = file.file.read(settings.MAX_UPLOAD_MB * 1024 * 1024 + 1)  # bounded read
    name = storage.sanitize_filename(file.filename or "file")
    ext, content_type = storage.validate_upload(name, data)
    key = f"shipments/{s.id}/{uuid.uuid4().hex}{ext}"
    storage.get_storage().save(key, data, content_type)
    doc = Document(shipment_id=s.id, doc_type=doc_type, filename=name, storage_key=key, content_type=content_type, size_bytes=len(data),
                   sha256=hashlib.sha256(data).hexdigest(), visible_to_customer=visible_to_customer, uploaded_by=user.id)
    db.add(doc)
    db.flush()
    audit.record(db, "DOCUMENT_UPLOADED", user=user, request=request, entity_type="document", entity_id=doc.id,
                 meta={"shipment_id": str(s.id), "tracking_number": s.tracking_number, "type": doc_type, "size": len(data), "customer_visible": visible_to_customer})
    db.commit()
    return doc

@router.delete("/documents/{doc_id}", status_code=204)
def delete_document(doc_id: uuid.UUID, request: Request, user: User = Depends(require_perms("documents:write")), db: Session = Depends(get_db)):
    doc = db.scalar(select(Document).where(Document.id == doc_id, Document.deleted_at.is_(None)))
    if not doc:
        raise err(404, "DOCUMENT_NOT_FOUND", "Document not found.")
    doc.deleted_at = datetime.now(UTC)  # soft delete; file kept for recovery/retention policy
    audit.record(db, "DOCUMENT_DELETED", user=user, request=request, entity_type="document", entity_id=doc.id, meta={"shipment_id": str(doc.shipment_id)})
    db.commit()
    return Response(status_code=204)

@router.get("/documents/{doc_id}/download")
def download_document(doc_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Staff may download any document. A customer only gets documents marked visible on THEIR OWN shipments."""
    doc = db.scalar(select(Document).where(Document.id == doc_id, Document.deleted_at.is_(None)))
    allowed = False
    if doc:
        if user.role != "CUSTOMER":
            allowed = has_perm(user.role, "shipments:read")
        else:
            s = db.get(Shipment, doc.shipment_id)
            allowed = bool(doc.visible_to_customer and s and s.deleted_at is None and s.customer.user_id == user.id)
    if not doc or not allowed:
        raise err(404, "DOCUMENT_NOT_FOUND", "Document not found.")  # 404, not 403: don't confirm it exists
    data = storage.get_storage().read(doc.storage_key)
    safe = doc.filename.replace('"', "")
    return Response(data, media_type=doc.content_type, headers={
        "Content-Disposition": f'attachment; filename="{safe}"', "X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"})