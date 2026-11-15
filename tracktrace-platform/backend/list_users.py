from app.db.session import SessionLocal
from app.models.user import User
db = SessionLocal()
for u in db.query(User).all():
    print(u.email, "|", u.role if hasattr(u, "role") else "?", "| active:", u.is_active, "| locked_until:", u.locked_until)
