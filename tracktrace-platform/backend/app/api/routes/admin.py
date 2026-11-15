"""Dashboard, reports and audit log (all numbers computed from the database)."""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.deps import require_perms
from app.db.session import get_db
from app.models import AuditLog, ContactMessage, QuoteRequest, ServiceType, Shipment, ShipmentStatus, User

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
def dashboard(user: User = Depends(require_perms("shipments:read")), db: Session = Depends(get_db)):
    live = Shipment.deleted_at.is_(None)
    counts = dict(db.execute(select(Shipment.status, func.count()).where(live).group_by(Shipment.status)).all())
    total = sum(counts.values())
    terminal = set(db.scalars(select(ShipmentStatus.code).where(ShipmentStatus.is_terminal.is_(True))).all())
    active = sum(n for s, n in counts.items() if s not in terminal)
    pending_quotes = db.scalar(select(func.count()).select_from(QuoteRequest).where(QuoteRequest.status.in_(("NEW", "IN_REVIEW")))) or 0
    unread = db.scalar(select(func.count()).select_from(ContactMessage).where(ContactMessage.status == "NEW")) or 0
    return {
        "total_shipments": total, "active_shipments": active, "in_transit": counts.get("IN_TRANSIT", 0),
        "out_for_delivery": counts.get("OUT_FOR_DELIVERY", 0), "delivered": counts.get("DELIVERED", 0),
        "delayed": counts.get("DELAYED", 0), "exceptions": counts.get("EXCEPTION", 0),
        "pending_quotes": pending_quotes, "unread_messages": unread, "by_status": counts,
    }


@router.get("/reports")
def reports(date_from: datetime | None = None, date_to: datetime | None = None, user: User = Depends(require_perms("reports:read")),
            db: Session = Depends(get_db)):
    conds = [Shipment.deleted_at.is_(None)]
    if date_from:
        conds.append(Shipment.created_at >= date_from)
    if date_to:
        conds.append(Shipment.created_at <= date_to)
    by_month = db.execute(select(func.to_char(func.date_trunc("month", Shipment.created_at), "YYYY-MM").label("m"), func.count()).where(*conds)
                          .group_by("m").order_by("m")).all()
    by_service = db.execute(select(func.coalesce(ServiceType.name["en"].astext, "Unspecified"), func.count()).select_from(Shipment)
                            .outerjoin(ServiceType, Shipment.service_type_id == ServiceType.id).where(*conds)
                            .group_by(ServiceType.name["en"].astext).order_by(desc(func.count()))).all()
    top_dest = db.execute(select(Shipment.destination, func.count()).where(*conds).group_by(Shipment.destination).order_by(desc(func.count())).limit(10)).all()
    delivered_n, avg_secs = db.execute(select(func.count(), func.avg(func.extract("epoch", Shipment.actual_delivery - Shipment.created_at)))
                                       .where(*conds, Shipment.actual_delivery.is_not(None))).one()
    on_time = db.execute(select(func.count()).where(*conds, Shipment.actual_delivery.is_not(None), Shipment.estimated_delivery.is_not(None),
                                                    Shipment.actual_delivery <= Shipment.estimated_delivery)).scalar() or 0
    with_eta = db.execute(select(func.count()).where(*conds, Shipment.actual_delivery.is_not(None), Shipment.estimated_delivery.is_not(None))).scalar() or 0
    quotes = dict(db.execute(select(QuoteRequest.status, func.count()).group_by(QuoteRequest.status)).all())
    return {
        "shipments_by_month": [{"month": m, "count": c} for m, c in by_month],
        "shipments_by_service": [{"service": s, "count": c} for s, c in by_service],
        "top_destinations": [{"destination": d, "count": c} for d, c in top_dest],
        "delivered_count": delivered_n, "avg_delivery_days": round(float(avg_secs) / 86400, 2) if avg_secs is not None else None,
        "delivered_on_or_before_eta": {"count": on_time, "of": with_eta},
        "quotes_by_status": quotes,
    }


@router.get("/audit-logs")
def audit_logs(action: str | None = None, entity_type: str | None = None, user_id: str | None = None, q: str | None = None,
               page: int = 1, page_size: int = 50, actor: User = Depends(require_perms("audit:read")), db: Session = Depends(get_db)):
    page, page_size = max(1, page), min(max(1, page_size), 200)
    conds = []
    if action:
        conds.append(AuditLog.action == action)
    if entity_type:
        conds.append(AuditLog.entity_type == entity_type)
    if user_id:
        conds.append(AuditLog.user_id == user_id)
    if q:
        conds.append(AuditLog.user_email.ilike("%" + q.replace("%", "\\%").replace("_", "\\_") + "%", escape="\\"))
    total = db.scalar(select(func.count()).select_from(AuditLog).where(*conds)) or 0
    rows = db.scalars(select(AuditLog).where(*conds).order_by(desc(AuditLog.created_at), desc(AuditLog.id)).limit(page_size).offset((page - 1) * page_size)).all()
    items = [{"id": r.id, "user_id": r.user_id, "user_email": r.user_email, "action": r.action, "entity_type": r.entity_type, "entity_id": r.entity_id,
              "metadata": r.meta, "ip_address": r.ip_address, "created_at": r.created_at} for r in rows]
    return {"items": items, "total": total, "page": page, "page_size": page_size}
