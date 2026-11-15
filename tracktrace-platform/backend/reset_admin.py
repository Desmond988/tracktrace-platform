from app.db.session import SessionLocal
from app.core.security import hash_password
from app.models.user import User
db = SessionLocal()
u = db.query(User).filter(User.email == "admin@example.com").first()
u.hashed_password = hash_password("AdminReset2026!")
u.failed_login_attempts = 0
u.locked_until = None
u.is_active = True
db.commit()
print("ADMIN RESET OK:", u.email, u.role)
