"""User model for JWT RBAC"""
import enum
from sqlalchemy import Column, Integer, String, DateTime, func
from .models import Base


class UserRole(str, enum.Enum):
    PATHOLOGY_STAFF = "pathology_staff"
    DOCTOR = "doctor"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default=UserRole.DOCTOR.value)
    display_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
