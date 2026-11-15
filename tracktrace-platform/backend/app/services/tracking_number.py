import re
import secrets

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.services import site_settings

# 32 symbols, no I/O/0/1 to avoid transcription errors. 8 chars ~ 1.1e12 combinations, random (not sequential/guessable).
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8
PREFIX_RE = re.compile(r"^[A-Z0-9]{2,8}$")
LOOKUP_RE = re.compile(r"^[A-Z0-9]{2,10}-[A-Z0-9]{3,20}$")


def normalize(raw: str) -> str:
    return re.sub(r"\s+", "", raw or "").upper()


def is_valid_format(value: str) -> bool:
    return bool(LOOKUP_RE.match(value))


def generate(prefix: str) -> str:
    return f"{prefix}-{''.join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))}"


def current_prefix(db: Session) -> str:
    prefix = str(site_settings.get(db, "tracking.prefix")).upper()
    if not PREFIX_RE.match(prefix):
        raise ValueError("Configured tracking prefix is invalid (2-8 letters/digits)")
    return prefix


def insert_with_unique_number(db: Session, shipment, max_attempts: int = 8):
    """Assigns a tracking number and flushes. The UNIQUE index is the real guarantee; on collision we retry
    inside a SAVEPOINT so the caller's transaction is not aborted."""
    prefix = current_prefix(db)
    for _ in range(max_attempts):
        shipment.tracking_number = generate(prefix)
        try:
            with db.begin_nested():
                db.add(shipment)
                db.flush()
            return shipment
        except IntegrityError as exc:
            if "uq_shipments_tracking_number" not in str(exc.orig):
                raise
            db.expunge(shipment) if shipment in db else None
    raise RuntimeError("Could not allocate a unique tracking number")
