from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import err
from app.core.ratelimit import limiter
from app.db.session import get_db
from app.models import Shipment
from app.schemas.shipment import PublicEvent, PublicTracking
from app.services import tracking_number as tn_service

router = APIRouter(prefix="/api/tracking", tags=["public tracking"])

@router.get("/{tracking_number}", response_model=PublicTracking, dependencies=[Depends(limiter("tracking", "RATE_LIMIT_TRACKING"))])
def track(tracking_number: str, response: Response, db: Session = Depends(get_db)):
    """Public lookup. Returns real database data only; exposes no customer or address details."""
    response.headers["Cache-Control"] = "no-store"
    number = tn_service.normalize(tracking_number)
    if not tn_service.is_valid_format(number):
        raise err(400, "INVALID_TRACKING_NUMBER", "That doesn't look like a valid tracking number. Check it and try again.")
    s = db.scalar(select(Shipment).where(Shipment.tracking_number == number, Shipment.deleted_at.is_(None)))
    if not s:
        raise err(404, "TRACKING_NOT_FOUND", "Tracking number not found.")
    events = sorted((e for e in s.events if e.is_public), key=lambda e: (e.event_timestamp, e.created_at))
    return PublicTracking(
        tracking_number=s.tracking_number, status=s.status_ref, origin=s.origin, destination=s.destination,
        current_location=s.current_location, created_at=s.created_at, estimated_delivery=s.estimated_delivery, actual_delivery=s.actual_delivery,
        service_type={"name": s.service_type.name} if s.service_type else None,
        pieces=s.pieces, updated_at=s.updated_at, events=[PublicEvent.model_validate(e) for e in events],
    )