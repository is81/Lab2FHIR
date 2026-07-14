"""初始化默认用户账户"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.db.models import SessionLocal, init_db
from src.db.user_models import User, UserRole
from src.auth.security import hash_password

init_db()

db = SessionLocal()
try:
    existing = db.query(User).first()
    if existing:
        print("用户已存在，跳过种子数据。")
        db.close()
        sys.exit(0)

    db.add_all([
        User(
            username="admin",
            password_hash=hash_password("admin123"),
            role=UserRole.PATHOLOGY_STAFF.value,
            display_name="管理员"
        ),
        User(
            username="doctor",
            password_hash=hash_password("doctor123"),
            role=UserRole.DOCTOR.value,
            display_name="王医生"
        ),
    ])
    db.commit()
    print("已创建默认用户:")
    print("  admin  / admin123  (pathology_staff - 病理科)")
    print("  doctor / doctor123 (doctor - 科室医生)")
finally:
    db.close()
