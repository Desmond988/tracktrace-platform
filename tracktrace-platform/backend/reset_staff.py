from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password
db = SessionLocal()
u = db.query(User).filter(User.email == "staff@example.com").first()
print(u.email)
u.password_hash = hash_password("StaffReset2026!")
db.commit()
print("RESET DONE")
