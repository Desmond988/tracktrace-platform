from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password
db = SessionLocal()
u = db.query(User).filter(User.email == "staff@example.com").first()
print(u.email, u.is_active, u.failed_login_count, u.locked_until)
u.password_hash = hash_password("StaffReset2026!")
u.failed_login_count = 0
u.locked_until = None
u.is_active = True
db.commit()
print("UNLOCKED + RESET DONE")
