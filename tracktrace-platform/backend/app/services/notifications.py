"""Notification architecture: EMAIL / SMS / WHATSAPP / IN_APP.

Honesty rule: a message is only marked SENT when a configured provider accepted it.
If a channel has no credentials the row is stored as SKIPPED_NOT_CONFIGURED - we never pretend it was sent.
"""
import logging
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Customer, Notification, Shipment, TrackingEvent
from app.services import i18n, site_settings

log = logging.getLogger("app.notifications")

TEMPLATES = {
    "en": {
        "subject": "Shipment {tn}: {status}",
        "body": "Update for shipment {tn}: {status}{loc}. You can follow it any time at {url}",
    },
    "fr": {
        "subject": "Expédition {tn} : {status}",
        "body": "Mise à jour de l'expédition {tn} : {status}{loc}. Suivez-la à tout moment sur {url}",
    },
}


def render(lang: str, shipment: Shipment, event: TrackingEvent) -> tuple[str, str]:
    label = i18n.localized(event.status_ref.label, lang)
    lang = lang if lang in TEMPLATES else "en"
    loc = f" ({event.location})" if event.location else ""
    url = f"{settings.FRONTEND_URL.rstrip('/')}/track?tn={shipment.tracking_number}"
    t = TEMPLATES[lang]
    return t["subject"].format(tn=shipment.tracking_number, status=label), t["body"].format(tn=shipment.tracking_number, status=label, loc=loc, url=url)


def queue_shipment_notifications(db: Session, shipment: Shipment, event: TrackingEvent) -> list[Notification]:
    """Creates Notification rows in the caller's transaction. Returns those needing external dispatch."""
    if not event.status_ref.notify_customer:
        return []
    customer: Customer = shipment.customer
    user = customer.user
    lang = user.preferred_language if user else "en"
    subject, body = render(lang, shipment, event)
    to_dispatch: list[Notification] = []
    tmpl = f"shipment_{event.status.lower()}"

    if user:  # in-app notification for the customer dashboard
        db.add(Notification(user_id=user.id, shipment_id=shipment.id, channel="IN_APP", template=tmpl, subject=subject, body=body,
                            status="SENT", sent_at=datetime.now(UTC)))
    def add(channel: str, recipient: str | None, enabled_setting: str, pref: bool):
        if not recipient or not pref:
            return
        row = Notification(user_id=user.id if user else None, shipment_id=shipment.id, channel=channel, template=tmpl,
                           recipient=recipient, subject=subject if channel == "EMAIL" else None, body=body,
                           status="PENDING")  # explicit: the column default is only applied at INSERT, too late for the check below
        if not site_settings.get(db, enabled_setting):
            row.status = "SKIPPED_NOT_CONFIGURED"
            row.error = "Channel disabled in settings"
        db.add(row)
        if row.status == "PENDING":
            to_dispatch.append(row)

    add("EMAIL", customer.email or (user.email if user else None), "notifications.email_enabled", customer.notify_email)
    add("SMS", customer.phone, "notifications.sms_enabled", customer.notify_sms)
    add("WHATSAPP", customer.phone, "notifications.whatsapp_enabled", customer.notify_whatsapp)
    db.flush()
    return to_dispatch


def _send_email(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = settings.SMTP_FROM, to, subject
    msg.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as s:
        if settings.SMTP_STARTTLS:
            s.starttls()
        if settings.SMTP_USER:
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        s.send_message(msg)


def _send_twilio(to: str, body: str, whatsapp: bool) -> None:
    frm = settings.TWILIO_WHATSAPP_FROM if whatsapp else settings.TWILIO_SMS_FROM
    prefix = "whatsapp:" if whatsapp else ""
    r = httpx.post(f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json",
                   data={"To": f"{prefix}{to}", "From": f"{prefix}{frm}" if not frm.startswith("whatsapp:") else frm, "Body": body},
                   auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN), timeout=15)
    r.raise_for_status()


def dispatch(notification_ids: list) -> None:
    """Background task: opens its own session, attempts delivery, records the honest outcome."""
    if not notification_ids:
        return
    db = SessionLocal()
    try:
        for nid in notification_ids:
            n = db.get(Notification, nid)
            if not n or n.status != "PENDING":
                continue
            try:
                if n.channel == "EMAIL":
                    if not settings.email_configured:
                        n.status, n.error = "SKIPPED_NOT_CONFIGURED", "SMTP not configured"
                    else:
                        _send_email(n.recipient, n.subject or "", n.body)
                        n.status, n.sent_at = "SENT", datetime.now(UTC)
                elif n.channel in ("SMS", "WHATSAPP"):
                    wa = n.channel == "WHATSAPP"
                    if not (settings.whatsapp_configured if wa else settings.sms_configured):
                        n.status, n.error = "SKIPPED_NOT_CONFIGURED", f"{n.channel} provider not configured"
                    else:
                        _send_twilio(n.recipient, n.body, wa)
                        n.status, n.sent_at = "SENT", datetime.now(UTC)
            except Exception as exc:  # provider failure must never break the request that triggered it
                log.warning("Notification %s failed: %s", nid, type(exc).__name__)
                n.status, n.error = "FAILED", f"{type(exc).__name__}"[:500]
            db.commit()
    finally:
        db.close()


def send_password_reset_email(to: str, link: str, lang: str) -> None:
    """Sends the reset link directly (never stored in the notifications table because it contains a secret)."""
    subject = "Réinitialisation de votre mot de passe" if lang == "fr" else "Reset your password"
    body = (f"Pour choisir un nouveau mot de passe, ouvrez ce lien (valable {settings.PASSWORD_RESET_MINUTES} minutes) :\n{link}\n\n"
            "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message."
            if lang == "fr" else
            f"To choose a new password, open this link (valid for {settings.PASSWORD_RESET_MINUTES} minutes):\n{link}\n\n"
            "If you didn't request this, you can ignore this message.")
    if not settings.email_configured:
        if not settings.is_production:
            log.warning("SMTP not configured. DEV ONLY reset link for %s: %s", to, link)
        else:
            log.error("SMTP not configured: password reset email could not be sent")
        return
    try:
        _send_email(to, subject, body)
    except Exception as exc:
        log.error("Password reset email failed: %s", type(exc).__name__)
