"""集中化配置管理 (Pydantic Settings)"""
import os
from pathlib import Path
from functools import lru_cache

# 项目根目录 (backend/src/config.py → backend/ → Lab2FHIR/)
_BACKEND_DIR = Path(__file__).resolve().parent.parent  # backend/
_PROJECT_ROOT = _BACKEND_DIR.parent                     # Lab2FHIR/


class Settings:
    """应用配置，从环境变量加载，有合理默认值"""

    # 环境
    ENV: str = os.getenv("LAB2FHIR_ENV", "development")
    DEBUG: bool = ENV == "development"

    # 数据库
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{_BACKEND_DIR / 'lab2fhir.db'}"
    )

    # 文件路径
    UPLOAD_DIR: str = os.getenv(
        "LAB2FHIR_UPLOAD_DIR",
        str(_BACKEND_DIR / "src" / "uploads")
    )
    PDF_TEST_DIR: str = os.getenv(
        "LAB2FHIR_PDF_TEST_DIR",
        str(_PROJECT_ROOT / "docs" / "pdf_test")
    )

    # 上传限制
    MAX_FILE_SIZE: int = int(os.getenv("LAB2FHIR_MAX_FILE_SIZE", str(50 * 1024 * 1024)))  # 50MB

    # CORS
    _cors_raw: str = os.getenv("CORS_ORIGINS", "*" if os.getenv("LAB2FHIR_ENV", "development") == "development" else "")
    CORS_ORIGINS: list[str] = [o.strip() for o in _cors_raw.split(",") if o.strip()]

    # Stats 缓存 TTL（秒）
    STATS_CACHE_TTL: int = int(os.getenv("LAB2FHIR_STATS_CACHE_TTL", "300"))

    # 日志
    LOG_LEVEL: str = os.getenv("LAB2FHIR_LOG_LEVEL", "INFO")

    # JWT 认证
    JWT_SECRET: str = os.getenv("LAB2FHIR_JWT_SECRET", "")
    JWT_EXPIRE_HOURS: int = int(os.getenv("LAB2FHIR_JWT_EXPIRE_HOURS", "48"))

    def __init__(self):
        if self.ENV == "production" and not self.JWT_SECRET:
            raise RuntimeError(
                "LAB2FHIR_JWT_SECRET 环境变量必须设置！\n"
                "生产环境请使用: export LAB2FHIR_JWT_SECRET=$(openssl rand -hex 32)"
            )
        if not self.JWT_SECRET:
            # 开发环境自动生成临时密钥
            import secrets
            self.JWT_SECRET = secrets.token_hex(32)

    @property
    def db_path(self) -> str:
        """返回 SQLite 数据库文件路径"""
        return self.DATABASE_URL.replace("sqlite:///", "")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """单例模式获取配置"""
    return Settings()
