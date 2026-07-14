"""API 集成测试（含认证）"""
import os
import pytest
from fastapi.testclient import TestClient
from src.config import get_settings

PDF_DIR = get_settings().PDF_TEST_DIR


@pytest.fixture
def public_client(db_session):
    """无认证的 TestClient（用于公开端点测试）"""
    from src.api.main import app
    from src.db.repository import get_db

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ====== 认证端点测试 ======

class TestAuthEndpoints:
    """POST /api/auth/login + GET /api/auth/me"""

    def test_login_success(self, public_client, db_session):
        """正确凭据应返回 JWT token"""
        from src.db.user_models import User
        from src.auth.security import hash_password
        user = User(username="login_test", password_hash=hash_password("test"),
                    role="pathology_staff", display_name="登录测试")
        db_session.add(user)
        db_session.commit()

        resp = public_client.post("/api/auth/login",
                                  json={"username": "login_test", "password": "test"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "login_test"
        assert data["user"]["role"] == "pathology_staff"

    def test_login_wrong_password(self, public_client, db_session):
        """错误密码应返回 401"""
        from src.db.user_models import User
        from src.auth.security import hash_password
        user = User(username="wrong_pw", password_hash=hash_password("test"),
                    role="doctor", display_name="错密用户")
        db_session.add(user)
        db_session.commit()

        resp = public_client.post("/api/auth/login",
                                  json={"username": "wrong_pw", "password": "WRONG"})
        assert resp.status_code == 401
        assert "用户名或密码错误" in resp.json()["detail"]

    def test_login_nonexistent_user(self, public_client):
        """不存在的用户返回 401"""
        resp = public_client.post("/api/auth/login",
                                  json={"username": "nobody", "password": "x"})
        assert resp.status_code == 401

    def test_me_with_valid_token(self, auth_client):
        """有效 token 返回用户信息"""
        resp = auth_client.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "test_staff"
        assert data["role"] == "pathology_staff"

    def test_me_without_token(self, public_client):
        """无 token 访问 /me 返回 401"""
        resp = public_client.get("/api/auth/me")
        assert resp.status_code == 401


# ====== 权限控制测试 ======

class TestAuthorization:
    """角色权限校验"""

    def test_doctor_cannot_convert(self, doctor_client):
        """医生角色 POST /convert → 403"""
        resp = doctor_client.post("/api/convert",
                                  files={"file": ("x.pdf", b"%PDF-fake", "application/pdf")})
        assert resp.status_code == 403

    def test_doctor_can_view_reports(self, doctor_client):
        """医生角色 GET /reports → 200"""
        resp = doctor_client.get("/api/reports")
        assert resp.status_code == 200

    def test_doctor_can_get_stats(self, doctor_client):
        """医生角色 GET /stats → 200"""
        resp = doctor_client.get("/api/stats")
        assert resp.status_code == 200

    def test_unauthenticated_convert(self, public_client):
        """未登录 POST /convert → 401"""
        resp = public_client.post("/api/convert",
                                  files={"file": ("x.pdf", b"%PDF", "application/pdf")})
        assert resp.status_code == 401

    def test_unauthenticated_reports(self, public_client):
        """未登录 GET /reports → 401"""
        resp = public_client.get("/api/reports")
        assert resp.status_code == 401

    def test_staff_can_convert(self, auth_client):
        """病理科角色 POST /convert → 200（文件校验先执行）"""
        resp = auth_client.post("/api/convert",
                                files={"file": ("x.txt", b"hello", "text/plain")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False  # 非 PDF 被拒绝（文件校验层面的错误，不是权限错误）


# ====== 功能端点测试（使用 auth_client） ======

class TestHealthEndpoint:
    """健康检查"""

    def test_health_returns_ok(self, auth_client):
        resp = auth_client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestStatsEndpoint:
    """统计端点"""

    def test_stats_returns_structure(self, auth_client):
        resp = auth_client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "type_counts" in data
        assert "recent" in data


class TestReportsEndpoints:
    """报告 CRUD"""

    def test_list_reports_empty(self, auth_client):
        resp = auth_client.get("/api/reports")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "items" in data

    def test_list_reports_with_pagination(self, auth_client):
        resp = auth_client.get("/api/reports?page=1&page_size=20")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_get_report_not_found(self, auth_client):
        resp = auth_client.get("/api/reports/99999")
        assert resp.status_code == 404

    def test_get_patient_reports_empty(self, auth_client):
        resp = auth_client.get("/api/patients/不存在/reports")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_convert_real_pdf(self, auth_client):
        """导入真实 PDF 并验证 DB 写入"""
        pdf_path = os.path.join(PDF_DIR, "2-5-2026_F2608174_DNA.pdf")
        with open(pdf_path, "rb") as f:
            resp = auth_client.post("/api/convert",
                                    files={"file": ("test_dna.pdf", f, "application/pdf")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["report_id"] > 0
        assert "fhir_bundle" in data

        detail = auth_client.get(f"/api/reports/{data['report_id']}")
        assert detail.status_code == 200
        assert detail.json()["report_type"] == "细胞学（妇科）"

    def test_deduplication_on_duplicate(self, auth_client):
        """重复导入同一文件应跳过"""
        pdf_path = os.path.join(PDF_DIR, "2-5-2026_F2608174_TCT报告.pdf")
        with open(pdf_path, "rb") as f:
            r1 = auth_client.post("/api/convert",
                                  files={"file": ("dup.pdf", f, "application/pdf")})
        assert r1.json()["success"] is True
        with open(pdf_path, "rb") as f:
            r2 = auth_client.post("/api/convert",
                                  files={"file": ("dup.pdf", f, "application/pdf")})
        assert r2.json()["skipped"] is True

    def test_search_after_import(self, auth_client):
        """导入后搜索"""
        pdf_path = os.path.join(PDF_DIR, "29-5-2026_N2604120_脱落细胞学报告.pdf")
        with open(pdf_path, "rb") as f:
            auth_client.post("/api/convert",
                             files={"file": ("s.pdf", f, "application/pdf")})

        resp = auth_client.get("/api/reports?search=姚秀刚")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_filter_by_report_type(self, auth_client):
        """按报告类型筛选"""
        with open(os.path.join(PDF_DIR, "2-5-2026_F2608174_DNA.pdf"), "rb") as f:
            auth_client.post("/api/convert",
                             files={"file": ("dna.pdf", f, "application/pdf")})

        resp = auth_client.get("/api/reports?report_type=细胞学（妇科）")
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["report_type"] == "细胞学（妇科）"


class TestPdfServing:
    """PDF 文件服务"""

    def test_pdf_not_found_for_nonexistent_report(self, auth_client):
        resp = auth_client.get("/api/reports/99999/pdf")
        assert resp.status_code == 404

    def test_pdf_path_traversal_blocked(self, auth_client):
        resp = auth_client.get("/api/pdf/../../etc/passwd")
        assert resp.status_code in (403, 404)
