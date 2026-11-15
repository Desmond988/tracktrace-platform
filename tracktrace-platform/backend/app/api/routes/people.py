"""Customers (records) and staff/user management."""
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_perms
from app.core.errors import err
from app.core.permissions import MANAGEABLE_ROLES
from app.core.security import hash_password, validate_password_strength
from app.db.session import get_db
from app.models import Customer, User
from app.schemas.auth import UserOut
from app.schemas.common import Page
from app.schemas.misc import CustomerCreate, CustomerOut, CustomerUpdate, LinkUserIn, UserCreate, UserUpdate
from app.services import audit

router = APIRouter(prefix="/api", tags=["customers & users"])


def _like(q: str) -> str:
    return "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


# ---------------- customers ----------------
@router.get("/customers", response_model=Page[CustomerOut])
def list_customers(q: str | None = None, page: int = 1, page_size: int = 20, user: User = Depends(require_perms("customers:read")),
                   db: Session = Depends(get_db)):
    page, page_size = max(1, page), min(max(1, page_size), 100)
    conds = [Customer.deleted_at.is_(None)]
    if q:
        p = _like(q.strip())
        conds.append(or_(Customer.name.ilike(p, escape="\\"), Customer.email.ilike(p, escape="\\"), Customer.company.ilike(p, escape="\\"), Customer.phone.ilike(p, escape="\\")))
    total = db.scalar(select(func.count()).select_from(Customer).where(*conds)) or 0
    items = db.scalars(select(Customer).where(*conds).order_by(Customer.name).limit(page_size).offset((page - 1) * page_size)).all()
    return Page[CustomerOut](items=items, total=total, page=page, page_size=page_size)


@router.post("/customers", response_model=CustomerOut, status_code=201)
def create_customer(body: CustomerCreate, request: Request, user: User = Depends(require_perms("customers:write")), db: Session = Depends(get_db)):
    c = Customer(**body.model_dump(), created_by=user.id)
    db.add(c)
    db.flush()
    audit.record(db, "CUSTOMER_CREATED", user=user, request=request, entity_type="customer", entity_id=c.id)
    db.commit()
    return c


def _customer(db: Session, cid: uuid.UUID) -> Customer:
    c = db.scalar(select(Customer).where(Customer.id == cid, Customer.deleted_at.is_(None)))
    if not c:
        raise err(404, "CUSTOMER_NOT_FOUND", "Customer not found.")
    return c


@router.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: uuid.UUID, user: User = Depends(require_perms("customers:read")), db: Session = Depends(get_db)):
    return _customer(db, customer_id)


@router.patch("/customers/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: uuid.UUID, body: CustomerUpdate, request: Request, user: User = Depends(require_perms("customers:write")),
                    db: Session = Depends(get_db)):
    c = _customer(db, customer_id)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        if k == "name" and v is None:
            continue
        setattr(c, k, v)
    audit.record(db, "CUSTOMER_UPDATED", user=user, request=request, entity_type="customer", entity_id=c.id, meta={"fields": sorted(data)})
    db.commit()
    return c


@router.post("/customers/{customer_id}/link-user", response_model=CustomerOut)
def link_user(customer_id: uuid.UUID, body: LinkUserIn, request: Request, user: User = Depends(require_perms("customers:write", "users:read")),
              db: Session = Depends(get_db)):
    """Explicit staff action: attach an existing customer login to a staff-created customer record.
    (We never auto-link by email, because emails are not verified at registration.)"""
    c = _customer(db, customer_id)
    if c.user_id:
        raise err(409, "ALREADY_LINKED", "This customer record already has a login.")
    target = db.scalar(select(User).where(func.lower(User.email) == body.email.lower(), User.role == "CUSTOMER", User.deleted_at.is_(None)))
    if not target:
        raise err(404, "USER_NOT_FOUND", "No customer account with that email.")
    if db.scalar(select(Customer.id).where(Customer.user_id == target.id)):
        raise err(409, "USER_ALREADY_LINKED", "That login is already linked to another customer record.")
    c.user_id = target.id
    audit.record(db, "CUSTOMER_LINKED", user=user, request=request, entity_type="customer", entity_id=c.id, meta={"user_id": str(target.id)})
    db.commit()
    return c


# ---------------- users ----------------
def _can_manage(actor: User, role: str) -> bool:
    return role in MANAGEABLE_ROLES.get(actor.role, set())


@router.get("/users", response_model=Page[UserOut])
def list_users(q: str | None = None, role: str | None = None, page: int = 1, page_size: int = 20,
               user: User = Depends(require_perms("users:read")), db: Session = Depends(get_db)):
    page, page_size = max(1, page), min(max(1, page_size), 100)
    conds = [User.deleted_at.is_(None)]
    if q:
        p = _like(q.strip())
        conds.append(or_(User.name.ilike(p, escape="\\"), User.email.ilike(p, escape="\\")))
    if role:
        conds.append(User.role == role)
    total = db.scalar(select(func.count()).select_from(User).where(*conds)) or 0
    items = db.scalars(select(User).where(*conds).order_by(desc(User.created_at)).limit(page_size).offset((page - 1) * page_size)).all()
    return Page[UserOut](items=items, total=total, page=page, page_size=page_size)


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(body: UserCreate, request: Request, actor: User = Depends(require_perms("users:write")), db: Session = Depends(get_db)):
    if not _can_manage(actor, body.role):
        raise err(403, "FORBIDDEN", "You cannot create users with that role.")
    if validate_password_strength(body.password):
        raise err(422, "WEAK_PASSWORD", "Choose a stronger password (at least 10 characters).")
    if db.scalar(select(User.id).where(func.lower(User.email) == body.email.lower(), User.deleted_at.is_(None))):
        raise err(409, "EMAIL_TAKEN", "A user with this email already exists.")
    u = User(name=body.name, email=body.email.lower(), phone=body.phone, password_hash=hash_password(body.password), role=body.role)
    db.add(u)
    db.flush()
    if body.role == "CUSTOMER":
        db.add(Customer(user_id=u.id, name=u.name, email=u.email, phone=u.phone, created_by=actor.id))
    audit.record(db, "USER_CREATED", user=actor, request=request, entity_type="user", entity_id=u.id, meta={"role": u.role})
    db.commit()
    return u


def _target(db: Session, uid: uuid.UUID) -> User:
    u = db.scalar(select(User).where(User.id == uid, User.deleted_at.is_(None)))
    if not u:
        raise err(404, "USER_NOT_FOUND", "User not found.")
    return u


def _other_super_admins(db: Session, exclude: uuid.UUID) -> int:
    return db.scalar(select(func.count()).select_from(User).where(User.role == "SUPER_ADMIN", User.is_active.is_(True), User.deleted_at.is_(None), User.id != exclude)) or 0


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: uuid.UUID, body: UserUpdate, request: Request, actor: User = Depends(require_perms("users:write")), db: Session = Depends(get_db)):
    u = _target(db, user_id)
    if not _can_manage(actor, u.role):
        raise err(403, "FORBIDDEN", "You cannot modify this user.")
    data = body.model_dump(exclude_unset=True)
    if "role" in data and data["role"] and data["role"] != u.role:
        if not _can_manage(actor, data["role"]):
            raise err(403, "FORBIDDEN", "You cannot assign that role.")
        if u.id == actor.id:
            raise err(409, "CANNOT_CHANGE_OWN_ROLE", "You cannot change your own role.")
        if u.role == "SUPER_ADMIN" and not _other_super_admins(db, u.id):
            raise err(409, "LAST_SUPER_ADMIN", "There must always be at least one active super admin.")
    if data.get("is_active") is False:
        if u.id == actor.id:
            raise err(409, "CANNOT_DEACTIVATE_SELF", "You cannot deactivate your own account.")
        if u.role == "SUPER_ADMIN" and not _other_super_admins(db, u.id):
            raise err(409, "LAST_SUPER_ADMIN", "There must always be at least one active super admin.")
    fields = []
    for k in ("name", "phone", "role", "is_active"):
        if k in data and data[k] is not None and getattr(u, k) != data[k]:
            setattr(u, k, data[k])
            fields.append(k)
            if k in ("role", "is_active"):
                u.token_version += 1  # existing sessions must re-authenticate under the new rules
    if data.get("new_password"):
        if validate_password_strength(data["new_password"]):
            raise err(422, "WEAK_PASSWORD", "Choose a stronger password (at least 10 characters).")
        u.password_hash, u.token_version = hash_password(data["new_password"]), u.token_version + 1
        fields.append("password")
    audit.record(db, "USER_UPDATED", user=actor, request=request, entity_type="user", entity_id=u.id, meta={"fields": fields})
    db.commit()
    return u


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: uuid.UUID, request: Request, actor: User = Depends(require_perms("users:write")), db: Session = Depends(get_db)):
    u = _target(db, user_id)
    if u.id == actor.id:
        raise err(409, "CANNOT_DELETE_SELF", "You cannot delete your own account.")
    if not _can_manage(actor, u.role):
        raise err(403, "FORBIDDEN", "You cannot delete this user.")
    if u.role == "SUPER_ADMIN" and not _other_super_admins(db, u.id):
        raise err(409, "LAST_SUPER_ADMIN", "There must always be at least one active super admin.")
    u.deleted_at, u.is_active, u.token_version = datetime.now(UTC), False, u.token_version + 1  # soft delete: history keeps its references
    audit.record(db, "USER_DELETED", user=actor, request=request, entity_type="user", entity_id=u.id, meta={"role": u.role})
    db.commit()
    return Response(status_code=204)
