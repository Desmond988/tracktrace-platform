"""Creates exactly one SUPER_ADMIN account. Safe to run against production - unlike seed_dev.py,
this creates nothing else (no demo shipments, no other accounts).

Usage:
  python scripts/create_admin.py --email admin@yourcompany.com --name "Jane Doe"
The password is prompted interactively (not passed as a CLI arg, so it never lands in shell history).
"""
import argparse
import getpass
import sys

sys.path.insert(0, ".")
from sqlalchemy import select

from app.core.security import hash_password, validate_password_strength
from app.db.session import SessionLocal
from app.models import User

parser = argparse.ArgumentParser()
parser.add_argument("--email", required=True)
parser.add_argument("--name", required=True)
args = parser.parse_args()

db = SessionLocal()
existing = db.scalar(select(User).where(User.email == args.email.lower()))
if existing:
    print(f"A user with email {args.email} already exists (role={existing.role}). Nothing was created.")
    raise SystemExit(1)

password = getpass.getpass("Set a password for the new SUPER_ADMIN: ")
confirm = getpass.getpass("Confirm password: ")
if password != confirm:
    print("Passwords did not match. Nothing was created.")
    raise SystemExit(1)
problems = validate_password_strength(password)
if problems:
    print(f"Password too weak: {problems}. Nothing was created.")
    raise SystemExit(1)

user = User(name=args.name, email=args.email.lower(), password_hash=hash_password(password), role="SUPER_ADMIN")
db.add(user)
db.commit()
print(f"Created SUPER_ADMIN: {user.email}")
