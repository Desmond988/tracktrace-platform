from app.db.session import SessionLocal
from app.core.security import hash_password, verify_password
from app.models.user import User
db = SessionLocal()
u = db.query(User).filter(User.email == "admin@example.com").first()
print("email:", u.email)
print("active:", u.is_active)
print("failed:", u.failed_login_attempts)
print("locked_until:", u.locked_until)
print("hash starts:", u.hashed_password[:20] if u.hashed_password else None)
print("verify AdminReset2026! =", verify_password("AdminReset2026!", u.hashed_password))
