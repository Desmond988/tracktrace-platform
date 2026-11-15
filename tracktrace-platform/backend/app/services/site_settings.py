"""Centralised, editable company/site settings. Defaults are PLACEHOLDERS, never invented company facts."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings as env
from app.models import SiteSetting

PLACEHOLDER = {
    "company.name": "FreightXpress Delivery",
    "company.legal_name": "FreightXpress Delivery",
    "company.address": "New York City, New York, United States",
    "company.phone": "[COMPANY PHONE]",
    "company.email": "[COMPANY EMAIL]",
    "company.registration": "[COMPANY REGISTRATION]",
    "company.certifications": "[COMPANY CERTIFICATIONS]",
    "company.business_hours": " Available 24/7",
    "company.logo_url": "",
    "company.favicon_url": "",
    "social.facebook": "", "social.linkedin": "", "social.x": "", "social.instagram": "", "social.youtube": "", "social.whatsapp": "",
    "footer.text": "",
    "seo.title": "FreightXpress Delivery | Freight and logistics",
    "seo.description": "Track your shipment and request freight and logistics services.",
    "locale.languages": ["en", "fr", "es", "de", "pt", "it", "nl", "pl", "ru", "tr", "ar", "zh", "ja", "ko", "hi", "sw"],
    "locale.default_language": "en",
    "locale.default_currency": "USD",
    "locale.timezone": "UTC",
    "tracking.prefix": env.TRACKING_PREFIX,
    "notifications.email_enabled": True,
    "notifications.sms_enabled": False,
    "notifications.whatsapp_enabled": False,
}
SENSITIVE_PREFIXES = ("tracking.", "notifications.", "locale.languages")


def is_sensitive(key: str) -> bool:
    return key.startswith(SENSITIVE_PREFIXES)


def is_public(key: str) -> bool:
    return not key.startswith("notifications.")


def get_all(db: Session) -> dict:
    merged = dict(PLACEHOLDER)
    for row in db.scalars(select(SiteSetting)):
        if row.key in PLACEHOLDER:
            merged[row.key] = row.value
    return merged


def get(db: Session, key: str):
    row = db.get(SiteSetting, key)
    return row.value if row is not None else PLACEHOLDER[key]
