"""初始化默认用户账户

环境变量:
  LAB2FHIR_ADMIN_PASSWORD  管理员密码（不设置则随机生成）
  LAB2FHIR_DOCTOR_PASSWORD 医生密码（不设置则随机生成）
"""
import sys
import os
import secrets
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

    admin_pw = os.getenv("LAB2FHIR_ADMIN_PASSWORD", secrets.token_urlsafe(12))
    doctor_pw = os.getenv("LAB2FHIR_DOCTOR_PASSWORD", secrets.token_urlsafe(12))

    db.add_all([
        User(
            username="admin",
            password_hash=hash_password(admin_pw),
            role=UserRole.PATHOLOGY_STAFF.value,
            display_name="管理员"
        ),
        User(
            username="doctor",
            password_hash=hash_password(doctor_pw),
            role=UserRole.DOCTOR.value,
            display_name="王医生"
        ),
    ])
    db.commit()
    print("已创建默认用户:")
    print(f"  admin  / {admin_pw}  (pathology_staff - 病理科)")
    print(f"  doctor / {doctor_pw} (doctor - 科室医生)")
    if not os.getenv("LAB2FHIR_ADMIN_PASSWORD"):
        print("\n⚠️  密码为随机生成，请妥善保存！通过环境变量设置固定密码：")
        print("   LAB2FHIR_ADMIN_PASSWORD=xxx LAB2FHIR_DOCTOR_PASSWORD=xxx python tools/seed_users.py")
finally:
    db.close()
