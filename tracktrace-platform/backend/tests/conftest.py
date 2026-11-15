import os
import uuid

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg://tnt:tnt_dev_pw@localhost:5432/tnt_test")

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.core import ratelimit
from app.core.security import hash_password
from app.db.session import SessionLocal, engine
from app.main import app
from app.models import Customer, User

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session", autouse=True)
def _migrate_db():
    """Wipes the test schema (not just alembic downgrade - leftover FK-referenced rows from a previous
    run can make downgrade fail) and re-applies every migration from scratch."""
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    os.environ["ALEMBIC_DATABASE_URL"] = os.environ["DATABASE_URL"]
    command.upgrade(cfg, "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def _rate_limit_state():
    ratelimit.reset()
    ratelimit.ENABLED = True
    yield
    ratelimit.ENABLED = True


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def make_user(db, *, role="CUSTOMER", email=None, password="Sup3rSecret!Pass", name="Test User", phone="+15550000000"):
    email = email or f"{role.lower()}-{uuid.uuid4().hex[:8]}@example.com"
    u = User(name=name, email=email, phone=phone, password_hash=hash_password(password), role=role)
    db.add(u)
    db.flush()
    if role == "CUSTOMER":
        db.add(Customer(user_id=u.id, name=name, email=email, phone=phone))
    db.commit()
    return u, password


def auth_headers(client: TestClient, email: str, password: str) -> dict:
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.cookies.get("access_token")
    return {"Authorization": f"Bearer {token}"}
