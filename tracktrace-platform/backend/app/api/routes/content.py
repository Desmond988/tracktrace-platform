"""Site settings, legal pages, FAQ, services, statuses, locations."""
import re
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_perms
from app.core.errors import err
from app.core.permissions import has_perm
from app.db.session import get_db
from app.models import Faq, LegalPage, Location, ServiceType, ShipmentStatus, SiteSetting, User
from app.schemas.common import ServiceOut, StatusOut
from app.services import audit, i18n, legal_defaults, site_settings
from app.services.tracking_number import PREFIX_RE

router = APIRouter(prefix="/api", tags=["content & settings"])
URL_RE = re.compile(r"^https?://[^\s]+$")


# ---------------- settings ----------------
@router.get("/public/settings")
def public_settings(db: Session = Depends(get_db)):
    return {k: v for k, v in site_settings.get_all(db).items() if site_settings.is_public(k)}


@router.get("/admin/settings")
def admin_settings(user: User = Depends(require_perms("settings:read")), db: Session = Depends(get_db)):
    return {"values": site_settings.get_all(db), "sensitive_keys": [k for k in site_settings.PLACEHOLDER if site_settings.is_sensitive(k)]}


class SettingsIn(BaseModel):
    values: dict[str, Any] = Field(min_length=1, max_length=60)


def _validate_setting(key: str, v: Any) -> Any:
    default = site_settings.PLACEHOLDER[key]
    if key == "tracking.prefix":
        v = str(v).strip().upper()
        if not PREFIX_RE.match(v):
            raise err(422, "INVALID_SETTING", "Tracking prefix must be 2-8 letters or digits.", key=key)
    elif key == "locale.languages":
        if not isinstance(v, list) or not v or not set(v) <= i18n.LANGUAGE_CODES:
            raise err(422, "INVALID_SETTING", f"Supported languages are: {', '.join(sorted(i18n.LANGUAGE_CODES))}.", key=key)
    elif key == "locale.default_language":
        if v not in i18n.LANGUAGE_CODES:
            raise err(422, "INVALID_SETTING", "Unsupported language.", key=key)
    elif key == "locale.default_currency":
        if not isinstance(v, str) or not re.match(r"^[A-Z]{3}$", v):
            raise err(422, "INVALID_SETTING", "Currency must be a 3-letter code such as USD.", key=key)
    elif isinstance(default, bool):
        if not isinstance(v, bool):
            raise err(422, "INVALID_SETTING", "Expected true or false.", key=key)
    elif isinstance(default, str):
        if not isinstance(v, str) or len(v) > 500:
            raise err(422, "INVALID_SETTING", "Expected text up to 500 characters.", key=key)
        if (key.startswith("social.") or key.endswith("_url")) and v and not URL_RE.match(v):
            raise err(422, "INVALID_SETTING", "Expected a full https:// URL.", key=key)
    return v


@router.put("/admin/settings")
def update_settings(body: SettingsIn, request: Request, user: User = Depends(require_perms("settings:write")), db: Session = Depends(get_db)):
    changed = {}
    for key, raw in body.values.items():
        if key not in site_settings.PLACEHOLDER:
            raise err(422, "UNKNOWN_SETTING", "Unknown setting.", key=key)
        if site_settings.is_sensitive(key) and not has_perm(user.role, "settings:sensitive"):
            raise err(403, "FORBIDDEN", "Only a super admin can change this setting.", key=key)
        value = _validate_setting(key, raw)
        old = site_settings.get(db, key)
        if old != value:
            row = db.get(SiteSetting, key)
            if row:
                row.value, row.updated_by = value, user.id
            else:
                db.add(SiteSetting(key=key, value=value, updated_by=user.id))
            changed[key] = {"from": old if site_settings.is_sensitive(key) else "(edited)", "to": value if site_settings.is_sensitive(key) else "(edited)"}
    if changed:
        audit.record(db, "SETTINGS_CHANGED", user=user, request=request, entity_type="settings", meta={"changed": changed})
    db.commit()
    return {"values": site_settings.get_all(db), "changed": sorted(changed)}


# ---------------- legal pages ----------------
# `title`/`body` are {language_code: text} dicts; a language missing from the dict falls back to
# English on the public site (see app.services.i18n.localized), so an untranslated page is never blank.
def _legal_dict(db: Session, slug: str) -> dict | None:
    row = db.get(LegalPage, slug)
    if row:
        return {"slug": row.slug, "title": row.title, "body": row.body, "legally_reviewed": row.legally_reviewed,
                "updated_at": row.updated_at, "review_note": None if row.legally_reviewed else legal_defaults.REVIEW_NOTE}
    return legal_defaults.default_page(slug)


@router.get("/legal")
def list_legal(db: Session = Depends(get_db)):
    out = []
    for slug in legal_defaults.SLUGS:
        d = _legal_dict(db, slug)
        out.append({"slug": slug, "title": d["title"]})
    return out


@router.get("/legal/{slug}")
def get_legal(slug: str, db: Session = Depends(get_db)):
    d = _legal_dict(db, slug)
    if not d:
        raise err(404, "NOT_FOUND", "Page not found.")
    return d


class LegalIn(BaseModel):
    title: dict[str, str]
    body: dict[str, str]
    legally_reviewed: bool = False

    @field_validator("title")
    @classmethod
    def _v_title(cls, v: dict[str, str]) -> dict[str, str]:
        return i18n.normalize_translations(v)

    @field_validator("body")
    @classmethod
    def _v_body(cls, v: dict[str, str]) -> dict[str, str]:
        cleaned = i18n.normalize_translations(v)
        for lang, text_ in cleaned.items():
            if len(text_) < 10:
                raise ValueError(f"Body text for '{lang}' is too short (minimum 10 characters).")
        return cleaned


@router.put("/admin/legal/{slug}")
def put_legal(slug: str, body: LegalIn, request: Request, user: User = Depends(require_perms("legal:write")), db: Session = Depends(get_db)):
    if slug not in legal_defaults.SLUGS:
        raise err(404, "NOT_FOUND", "Page not found.")
    row = db.get(LegalPage, slug)
    if row:
        row.title, row.body, row.legally_reviewed, row.updated_by = body.title, body.body, body.legally_reviewed, user.id
    else:
        db.add(LegalPage(slug=slug, title=body.title, body=body.body, legally_reviewed=body.legally_reviewed, updated_by=user.id))
    audit.record(db, "LEGAL_PAGE_UPDATED", user=user, request=request, entity_type="legal_page", entity_id=slug,
                 meta={"reviewed": body.legally_reviewed, "languages": sorted(body.title)})
    db.commit()
    return _legal_dict(db, slug)


# ---------------- FAQ ----------------
class FaqIn(BaseModel):
    question: dict[str, str]
    answer: dict[str, str]
    sort_order: int = 0
    is_published: bool = True

    @field_validator("question")
    @classmethod
    def _v_q(cls, v: dict[str, str]) -> dict[str, str]:
        return i18n.normalize_translations(v)

    @field_validator("answer")
    @classmethod
    def _v_a(cls, v: dict[str, str]) -> dict[str, str]:
        return i18n.normalize_translations(v)


@router.get("/faq")
def list_faq(db: Session = Depends(get_db)):
    rows = db.scalars(select(Faq).where(Faq.is_published.is_(True)).order_by(Faq.sort_order)).all()
    return [{"id": f.id, "question": f.question, "answer": f.answer} for f in rows]


@router.post("/admin/faq", status_code=201)
def create_faq(body: FaqIn, request: Request, user: User = Depends(require_perms("faq:write")), db: Session = Depends(get_db)):
    f = Faq(question=body.question, answer=body.answer, sort_order=body.sort_order, is_published=body.is_published)
    db.add(f)
    db.flush()
    audit.record(db, "FAQ_CREATED", user=user, request=request, entity_type="faq", entity_id=f.id, meta={"languages": sorted(body.question)})
    db.commit()
    return {"id": f.id}


# ---------------- supported languages ----------------
@router.get("/languages")
def list_languages():
    """The supported-language list, for the frontend's language picker."""
    return [{"code": code, "english_name": en, "native_name": native, "rtl": rtl} for code, (en, native, rtl) in i18n.SUPPORTED_LANGUAGES.items()]


# ---------------- services / statuses / locations ----------------
@router.get("/services", response_model=list[ServiceOut])
def list_services(db: Session = Depends(get_db)):
    return db.scalars(select(ServiceType).where(ServiceType.is_active.is_(True)).order_by(ServiceType.sort_order)).all()


@router.get("/statuses", response_model=list[StatusOut])
def list_statuses(include_inactive: bool = False, db: Session = Depends(get_db)):
    stmt = select(ShipmentStatus).order_by(ShipmentStatus.sort_order)
    if not include_inactive:
        stmt = stmt.where(ShipmentStatus.is_active.is_(True))
    return db.scalars(stmt).all()


class StatusIn(BaseModel):
    code: str = Field(pattern="^[A-Z][A-Z0-9_]{2,39}$")
    label: dict[str, str] = Field(description='{"en": "...", "fr": "...", ...} - "en" is required')
    sort_order: int = 0
    is_terminal: bool = False
    is_problem: bool = False
    is_active: bool = True
    notify_customer: bool = True

    @field_validator("label")
    @classmethod
    def _validate_label(cls, v: dict[str, str]) -> dict[str, str]:
        return i18n.normalize_translations(v)


class StatusPatch(BaseModel):
    label: dict[str, str] | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    notify_customer: bool | None = None

    @field_validator("label")
    @classmethod
    def _validate_label(cls, v: dict[str, str] | None) -> dict[str, str] | None:
        return i18n.normalize_translations(v) if v is not None else v


@router.post("/admin/statuses", response_model=StatusOut, status_code=201)
def create_status(body: StatusIn, request: Request, user: User = Depends(require_perms("statuses:manage")), db: Session = Depends(get_db)):
    if db.get(ShipmentStatus, body.code):
        raise err(409, "STATUS_EXISTS", "A status with that code already exists.")
    s = ShipmentStatus(**body.model_dump())
    db.add(s)
    audit.record(db, "STATUS_CONFIG_CHANGED", user=user, request=request, entity_type="status", entity_id=body.code, meta={"created": True})
    db.commit()
    return s


@router.patch("/admin/statuses/{code}", response_model=StatusOut)
def patch_status(code: str, body: StatusPatch, request: Request, user: User = Depends(require_perms("statuses:manage")), db: Session = Depends(get_db)):
    s = db.get(ShipmentStatus, code)
    if not s:
        raise err(404, "NOT_FOUND", "Status not found.")
    data = body.model_dump(exclude_unset=True, exclude_none=True)
    for k, v in data.items():
        setattr(s, k, v)
    audit.record(db, "STATUS_CONFIG_CHANGED", user=user, request=request, entity_type="status", entity_id=code, meta={"fields": sorted(data)})
    db.commit()
    return s


class LocationIn(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str | None = Field(default=None, max_length=20)
    type: str = Field(default="OFFICE", pattern="^(OFFICE|WAREHOUSE|HUB|PORT|AIRPORT|OTHER)$")
    address_line: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    country_code: str | None = Field(default=None, pattern="^[A-Z]{2}$")
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=254)
    is_public: bool = False
    is_active: bool = True


def _loc(loc: Location) -> dict:
    return {c.name: getattr(loc, c.name) for c in Location.__table__.columns if c.name not in ("created_at", "updated_at")}


@router.get("/locations")
def public_locations(db: Session = Depends(get_db)):
    rows = db.scalars(select(Location).where(Location.is_public.is_(True), Location.is_active.is_(True)).order_by(Location.name)).all()
    return [_loc(loc) for loc in rows]


@router.get("/admin/locations")
def admin_locations(user: User = Depends(require_perms("shipments:read")), db: Session = Depends(get_db)):
    return [_loc(loc) for loc in db.scalars(select(Location).where(Location.is_active.is_(True)).order_by(Location.name)).all()]


@router.post("/admin/locations", status_code=201)
def create_location(body: LocationIn, request: Request, user: User = Depends(require_perms("locations:manage")), db: Session = Depends(get_db)):
    loc = Location(**body.model_dump())
    db.add(loc)
    db.flush()
    audit.record(db, "LOCATION_CREATED", user=user, request=request, entity_type="location", entity_id=loc.id)
    db.commit()
    return _loc(loc)
