from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import verify_password
db = SessionLocal()
u = db.query(User).filter(User.email == "staff@example.com").first()
print("verify:", verify_password("StaffReset2026!", u.password_hash))
print("hash starts:", u.password_hash[:20])
