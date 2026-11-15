from app.db.session import SessionLocal
from app.core.security import hash_password, verify_password
from app.models.user import User
db = SessionLocal()
u = db.query(User).filter(User.email == "admin@example.com").first()
u.password_hash = hash_password("AdminReset2026!")
u.failed_login_count = 0
u.locked_until = None
u.is_active = True
db.commit()
print("RESET OK:", u.email, u.role)
print("failed:", u.failed_login_count, "locked:", u.locked_until)
print("verify =", verify_password("AdminReset2026!", u.password_hash))
