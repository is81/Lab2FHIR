"""数据库模型、FTS5 全文索引、Stats 缓存"""
import time
import threading
import logging
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Text, JSON, func, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from ..config import get_settings

logger = logging.getLogger("lab2fhir.db")

_settings = get_settings()
DATABASE_URL = _settings.DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pathology_id = Column(String(50), index=True, comment="病理号")
    patient_name = Column(String(100), index=True, comment="患者姓名")
    gender = Column(String(10), comment="性别")
    age = Column(Integer, comment="年龄")
    report_type = Column(String(50), index=True, comment="报告类型")
    report_date = Column(Date, comment="报告日期")
    sample_date = Column(Date, comment="采样日期")
    hospital = Column(String(200), comment="送检医院")
    department = Column(String(100), comment="送检科室")
    doctor = Column(String(100), comment="送检医生")
    diagnosis = Column(Text, comment="诊断结论全文")
    diagnosis_summary = Column(String(500), comment="诊断摘要")
    status = Column(String(20), default="pending")
    raw_text = Column(Text, comment="PDF提取的原始文本")
    parsed_data = Column(JSON, comment="解析后的结构化数据")
    fhir_bundle = Column(JSON, comment="FHIR Bundle JSON")
    pdf_filename = Column(String(500), comment="原始PDF文件名")
    pdf_path = Column(String(1000), comment="原始PDF存储路径")
    created_at = Column(DateTime, server_default=func.now())


# ====== FTS5 全文索引 ======

def _get_db_path() -> str:
    """获取 SQLite 数据库文件路径"""
    return DATABASE_URL.replace("sqlite:///", "")


def init_db():
    """初始化数据库（优先使用 Alembic 迁移，回退到 create_all）"""
    try:
        from alembic.config import Config
        from alembic import command
        import os
        alembic_ini = os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")
        if os.path.exists(alembic_ini):
            cfg = Config(alembic_ini)
            command.upgrade(cfg, "head")
            logger.info("DB migrated via Alembic")
            return
    except Exception as e:
        logger.info(f"Alembic migration skipped, using create_all: {e}")
    # 回退：直接建表（开发/首次安装）
    Base.metadata.create_all(bind=engine)
    logger.info("DB created via create_all")


def init_fts():
    """初始化 FTS5 全文索引（通过 SQLAlchemy raw_connection 保证连接一致性）"""
    try:
        with engine.connect() as conn:
            conn.execute(
                __import__('sqlalchemy').text(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS reports_fts USING fts5("
                    "patient_name, pathology_id, diagnosis, raw_text, tokenize='unicode61')"
                )
            )
            conn.commit()
    except Exception as e:
        logger.warning(f"FTS5 init skipped: {e}")


def rebuild_fts():
    """重建 FTS5 索引（从 reports 表同步数据）"""
    try:
        db = SessionLocal()
        reports = db.query(Report).all()
        with engine.connect() as conn:
            conn.execute(__import__('sqlalchemy').text("DELETE FROM reports_fts"))
            for r in reports:
                conn.execute(
                    __import__('sqlalchemy').text(
                        "INSERT INTO reports_fts(rowid, patient_name, pathology_id, diagnosis, raw_text) "
                        "VALUES (:rid, :pn, :pid, :diag, :raw)"
                    ),
                    {"rid": r.id, "pn": r.patient_name or "", "pid": r.pathology_id or "",
                     "diag": r.diagnosis or "", "raw": r.raw_text or ""}
                )
            conn.commit()
        db.close()
        logger.info(f"FTS5 rebuilt: {len(reports)} records indexed")
    except Exception as e:
        logger.warning(f"FTS5 rebuild skipped: {e}")


# 1.4 修复：FTS 同步异常记录日志而非静默吞掉
@event.listens_for(Report, "after_insert")
@event.listens_for(Report, "after_update")
def _sync_fts(mapper, connection, target):
    try:
        connection.execute(
            __import__('sqlalchemy').text("DELETE FROM reports_fts WHERE rowid = :rid"),
            {"rid": target.id}
        )
        connection.execute(
            __import__('sqlalchemy').text(
                "INSERT INTO reports_fts(rowid, patient_name, pathology_id, diagnosis, raw_text) "
                "VALUES (:rid, :pn, :pid, :diag, :raw)"
            ),
            {"rid": target.id, "pn": target.patient_name or "", "pid": target.pathology_id or "",
             "diag": target.diagnosis or "", "raw": target.raw_text or ""}
        )
    except Exception as e:
        logger.error(f"FTS sync failed for report {target.id}: {e}")


# ====== Stats 缓存（线程安全） ======

_stats_cache: dict = {"data": None, "ts": 0.0}
_stats_lock = threading.Lock()
STATS_CACHE_TTL = _settings.STATS_CACHE_TTL

# 4.3/6.3 修复：统一标签映射 + 报告类型枚举
from .enums import TYPE_LABELS, ReportType, LOINC_CODES, LOINC_DISPLAYS
# 确保 User 模型被导入（Alembic 自动发现）
from .user_models import User  # noqa: F401


def get_stats_cached() -> dict:
    """带缓存的统计查询（线程安全）"""
    now = time.time()
    with _stats_lock:
        if _stats_cache["data"] is not None and (now - _stats_cache["ts"]) < STATS_CACHE_TTL:
            return _stats_cache["data"]

    # 1.7 修复：提前提取为纯 Python 字典，避免 DetachedInstanceError
    db = SessionLocal()
    try:
        from sqlalchemy import func as sqlfunc
        total = db.query(Report).count()
        type_counts = {}
        for row in db.query(Report.report_type, sqlfunc.count(Report.id)).group_by(Report.report_type).all():
            if row[0]:
                type_counts[row[0]] = row[1]
        recent_objs = db.query(Report).order_by(Report.created_at.desc()).limit(5).all()

        data = {
            "total": total,
            "type_counts": type_counts,
            "recent": [
                {
                    "id": r.id, "pathology_id": r.pathology_id,
                    "patient_name": r.patient_name, "report_type": r.report_type,
                    "report_type_label": TYPE_LABELS.get(r.report_type, r.report_type or ""),
                    "diagnosis_summary": r.diagnosis_summary,
                    "report_date": str(r.report_date) if r.report_date else None,
                    "created_at": str(r.created_at) if r.created_at else None
                } for r in recent_objs
            ]
        }
    finally:
        db.close()

    with _stats_lock:
        _stats_cache["data"] = data
        _stats_cache["ts"] = now
    return data


def invalidate_stats_cache():
    with _stats_lock:
        _stats_cache["data"] = None
        _stats_cache["ts"] = 0.0
