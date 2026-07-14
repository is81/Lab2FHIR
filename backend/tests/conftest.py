"""测试夹具和共享数据"""
import os
import sys
import pytest

# 确保 backend/ 在 sys.path 中
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from src.config import get_settings
from src.db.models import Base, init_db, init_fts
from src.extractors.base import extract_text

PDF_TEST_DIR = os.path.join(
    os.path.dirname(_BACKEND_DIR), "docs", "pdf_test"
)


# ====== PDF 文本 fixtures ======

@pytest.fixture(scope="module")
def dna_text():
    """DNA 倍体报告原始文本"""
    path = os.path.join(PDF_TEST_DIR, "2-5-2026_F2608174_DNA.pdf")
    return extract_text(path)


@pytest.fixture(scope="module")
def tct_text():
    """TCT 液基细胞学报告原始文本"""
    path = os.path.join(PDF_TEST_DIR, "2-5-2026_F2608174_TCT报告.pdf")
    return extract_text(path)


@pytest.fixture(scope="module")
def hpv_text():
    """HPV 基因分型报告原始文本"""
    path = os.path.join(PDF_TEST_DIR, "2-5-2026_V2605675_HPV诊断报告.pdf")
    return extract_text(path)


@pytest.fixture(scope="module")
def cytology_text():
    """细胞学（非妇科）报告原始文本"""
    path = os.path.join(PDF_TEST_DIR, "29-5-2026_N2604120_脱落细胞学报告.pdf")
    return extract_text(path)


@pytest.fixture(scope="module")
def pathology_text_2615599():
    """常规病理报告 2615599 原始文本"""
    path = os.path.join(PDF_TEST_DIR, "2-5-2026_2615599.pdf")
    return extract_text(path)


@pytest.fixture(scope="module")
def pathology_text_2615597():
    """常规病理报告 2615597 原始文本"""
    path = os.path.join(PDF_TEST_DIR, "6-5-2026_2615597.pdf")
    return extract_text(path)


# ====== 数据库 fixtures ======

@pytest.fixture
def db_session(tmp_path):
    """每个测试独立的数据库会话（临时文件 SQLite）"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import src.db.models as db_models

    db_file = str(tmp_path / "test.db")
    db_url = f"sqlite:///{db_file}"

    # 保存原始 engine/session
    _orig_engine = db_models.engine
    _orig_SessionLocal = db_models.SessionLocal

    # 替换为测试数据库
    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(bind=test_engine)
    db_models.engine = test_engine
    db_models.SessionLocal = TestSessionLocal

    # 建表 + FTS5
    db_models.Base.metadata.create_all(bind=test_engine)
    with test_engine.connect() as conn:
        import sqlalchemy as sa
        try:
            conn.execute(sa.text(
                "CREATE VIRTUAL TABLE IF NOT EXISTS reports_fts USING fts5("
                "patient_name, pathology_id, diagnosis, raw_text, tokenize='unicode61')"
            ))
            conn.commit()
        except Exception:
            pass

    # 创建 users 表（user_models.py 的 User 已注册到 Base.metadata）
    from src.db.user_models import User
    from src.auth.security import hash_password

    db = TestSessionLocal()
    yield db
    db.close()

    # 恢复原始 engine/session
    db_models.engine = _orig_engine
    db_models.SessionLocal = _orig_SessionLocal
    test_engine.dispose()


# ====== Auth fixtures ======

@pytest.fixture
def auth_client(db_session):
    """带 JWT 认证的 TestClient（pathology_staff 角色）"""
    from fastapi.testclient import TestClient
    from src.api.main import app
    from src.db.repository import get_db
    from src.db.user_models import User
    from src.auth.security import hash_password, create_access_token

    # 创建测试用户
    user = User(
        username="test_staff",
        password_hash=hash_password("test"),
        role="pathology_staff",
        display_name="测试管理员"
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token({"sub": "test_staff", "role": "pathology_staff"})

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def doctor_client(db_session):
    """带 JWT 认证的 TestClient（doctor 角色，仅查看权限）"""
    from fastapi.testclient import TestClient
    from src.api.main import app
    from src.db.repository import get_db
    from src.db.user_models import User
    from src.auth.security import hash_password, create_access_token

    # 创建测试医生
    user = User(
        username="test_doctor",
        password_hash=hash_password("test"),
        role="doctor",
        display_name="测试医生"
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token({"sub": "test_doctor", "role": "doctor"})

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})
    yield client
    app.dependency_overrides.clear()
