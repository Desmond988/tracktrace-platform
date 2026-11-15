"""DEVELOPMENT-ONLY seed data. Never run against production.

Creates:
  - one SUPER_ADMIN account (credentials printed once, not committed anywhere)
  - a STAFF account
  - two demo customers with logins
  - three demo shipments: DEMO-001 (in transit), DEMO-002 (delivered), DEMO-003 (exception)

Usage:
  ENVIRONMENT=development python scripts/seed_dev.py
"""
import secrets
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

sys.path.insert(0, ".")
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Customer, Shipment, ShipmentItem, TrackingEvent, User

if settings.is_production:
    print("Refusing to seed: ENVIRONMENT=production. This script is for development only.")
    raise SystemExit(1)

db = SessionLocal()


def rand_pw() -> str:
    return secrets.token_urlsafe(12)


def get_or_create_user(email: str, name: str, role: str, phone: str | None = None) -> tuple[User, str | None]:
    u = db.scalar(select(User).where(User.email == email))
    if u:
        return u, None
    pw = rand_pw()
    u = User(name=name, email=email, phone=phone, password_hash=hash_password(pw), role=role, is_active=True)
    db.add(u)
    db.flush()
    return u, pw


def get_or_create_customer(user: User) -> Customer:
    c = db.scalar(select(Customer).where(Customer.user_id == user.id))
    if c:
        return c
    c = Customer(user_id=user.id, name=user.name, email=user.email, phone=user.phone)
    db.add(c)
    db.flush()
    return c


printed_credentials = []

admin, admin_pw = get_or_create_user("admin@example.com", "Demo Super Admin", "SUPER_ADMIN")
if admin_pw:
    printed_credentials.append(("SUPER_ADMIN", admin.email, admin_pw))

staff, staff_pw = get_or_create_user("staff@example.com", "Demo Staff", "STAFF")
if staff_pw:
    printed_credentials.append(("STAFF", staff.email, staff_pw))

cust1_user, cust1_pw = get_or_create_user("customer1@example.com", "Demo Customer One", "CUSTOMER", phone="+1 555 0100")
if cust1_pw:
    printed_credentials.append(("CUSTOMER", cust1_user.email, cust1_pw))
customer1 = get_or_create_customer(cust1_user)

cust2_user, cust2_pw = get_or_create_user("customer2@example.com", "Demo Customer Two", "CUSTOMER", phone="+1 555 0101")
if cust2_pw:
    printed_credentials.append(("CUSTOMER", cust2_user.email, cust2_pw))
customer2 = get_or_create_customer(cust2_user)

db.flush()

now = datetime.now(UTC)


def demo_shipment(tracking_number: str, customer: Customer, origin: str, destination: str, events: list[tuple[str, str, str, int]]):
    """events: list of (status, location, description, days_ago)."""
    existing = db.scalar(select(Shipment).where(Shipment.tracking_number == tracking_number))
    if existing:
        return existing
    final_status, final_location, _, _ = events[-1]
    s = Shipment(tracking_number=tracking_number, customer_id=customer.id, origin=origin, destination=destination,
                current_location=final_location, status=final_status, pieces=1,
                cargo_description="[DEV SEED DATA] General cargo, not a real shipment.",
                estimated_delivery=now + timedelta(days=2), created_by=admin.id)
    if final_status == "DELIVERED":
        s.actual_delivery = now - timedelta(days=events[-1][3])
        s.estimated_delivery = s.actual_delivery
    db.add(s)
    db.flush()
    s.items = [ShipmentItem(shipment_id=s.id, description="1 pallet, general goods", quantity=1)]
    for status, location, desc, days_ago in events:
        db.add(TrackingEvent(shipment_id=s.id, status=status, location=location, description=desc,
                             event_timestamp=now - timedelta(days=days_ago), created_by=admin.id))
    db.flush()
    return s


demo_shipment("DEMO-001", customer1, "Toronto, CA", "Vancouver, CA", [
    ("SHIPMENT_CREATED", "Toronto, CA", "[DEV SEED DATA] Shipment created", 4),
    ("PICKED_UP", "Toronto, CA", "[DEV SEED DATA] Picked up from sender", 3),
    ("IN_TRANSIT", "Winnipeg, CA", "[DEV SEED DATA] In transit", 1),
])
demo_shipment("DEMO-002", customer1, "Montreal, CA", "Halifax, CA", [
    ("SHIPMENT_CREATED", "Montreal, CA", "[DEV SEED DATA] Shipment created", 6),
    ("IN_TRANSIT", "Quebec City, CA", "[DEV SEED DATA] In transit", 4),
    ("OUT_FOR_DELIVERY", "Halifax, CA", "[DEV SEED DATA] Out for delivery", 1),
    ("DELIVERED", "Halifax, CA", "[DEV SEED DATA] Delivered, signed for", 0),
])
demo_shipment("DEMO-003", customer2, "Calgary, CA", "Ottawa, CA", [
    ("SHIPMENT_CREATED", "Calgary, CA", "[DEV SEED DATA] Shipment created", 5),
    ("IN_TRANSIT", "Regina, CA", "[DEV SEED DATA] In transit", 3),
    ("EXCEPTION", "Winnipeg, CA", "[DEV SEED DATA] Delay due to weather", 1),
])

db.commit()
print("Development seed data applied.")
print("Demo tracking numbers: DEMO-001, DEMO-002, DEMO-003")
if printed_credentials:
    print("\nNewly created accounts (save these now - the password is not stored anywhere else):")
    for role, email, pw in printed_credentials:
        print(f"  {role:<12} {email:<28} {pw}")
else:
    print("\nNo new accounts were created (they already existed).")
