"""数据访问层"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from .models import Report, SessionLocal, engine, get_stats_cached, invalidate_stats_cache
from .enums import TYPE_LABELS

logger = logging.getLogger("lab2fhir.repository")

# 7.1 修复：解析器注册表（消除 if/elif 链）
PARSER_REGISTRY = {}
try:
    from ..parsers.dna_parser import parse_dna
    from ..parsers.tct_parser import parse_tct
    from ..parsers.hpv_parser import parse_hpv
    from ..parsers.gastric_parser import parse_gastric
    from ..parsers.cytology_parser import parse_cytology
    from ..parsers.pathology_parser import parse_pathology
    PARSER_REGISTRY = {
        "细胞学（妇科）": parse_tct,   # 默认用 TCT parser，DNA 特殊处理
        "HPV检测": parse_hpv,
        "细胞学（非妇科）": parse_cytology,
        "常规病理": parse_pathology,
    }
    # DNA 解析器单独映射（通过文本关键词区分）
    _DNA_KEYWORDS = ["DNA定量", "DNA倍体", "DNA指数"]
except ImportError:
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# FTS5 特殊字符转义表
_FTS_ESCAPE = str.maketrans({c: f'"{c}"' for c in '^*-()'})

# 同报告去重键字段
_DUP_CHECK_FIELDS = ["pathology_id", "report_type"]


class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    # 2.2 修复：去重方法移入 Repository
    def exists(self, pathology_id: str, report_type: str) -> bool:
        if not pathology_id:
            return False
        return self.db.query(Report).filter(
            Report.pathology_id == pathology_id,
            Report.report_type == report_type
        ).first() is not None

    def list_reports(
        self,
        search: str = None,
        report_type: str = None,
        date_from: str = None,
        date_to: str = None,
        page: int = 1,
        page_size: int = 10
    ):
        query = self.db.query(Report)

        if search:
            fts_ids = self._fts_search(search)
            if fts_ids is not None and len(fts_ids) > 0:
                query = query.filter(Report.id.in_(fts_ids))
            else:
                query = query.filter(
                    or_(
                        Report.patient_name.contains(search),
                        Report.pathology_id.contains(search),
                        Report.diagnosis.contains(search),
                        Report.diagnosis_summary.contains(search)
                    )
                )

        if report_type:
            query = query.filter(Report.report_type == report_type)

        if date_from:
            query = query.filter(Report.report_date >= date_from)
        if date_to:
            query = query.filter(Report.report_date <= date_to)

        total = query.count()
        items = query.order_by(Report.created_at.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def _fts_search(self, query_str: str):
        """2.6 修复：FTS5 搜索输入校验 + 特殊字符转义"""
        if not query_str or len(query_str) > 200:
            return None
        try:
            safe = query_str.strip()[:200]
            # 转义 FTS5 特殊字符
            for ch in ['*', '"', "'", '^', '-', '(', ')']:
                safe = safe.replace(ch, ' ')
            safe = safe.strip()
            if not safe:
                return []
            terms = " ".join(f'{t}*' for t in safe.split() if len(t) >= 1)
            if not terms:
                return []

            with engine.connect() as conn:
                rows = conn.execute(
                    __import__('sqlalchemy').text(
                        "SELECT rowid FROM reports_fts WHERE reports_fts MATCH :q LIMIT 2000"
                    ),
                    {"q": terms}
                ).fetchall()
            return [r[0] for r in rows] if rows else []
        except Exception as e:
            logger.debug(f"FTS search fallback: {e}")
            return None

    def get_report(self, report_id: int):
        return self.db.query(Report).filter(Report.id == report_id).first()

    def get_patient_reports(self, patient_name: str):
        return self.db.query(Report).filter(
            Report.patient_name == patient_name
        ).order_by(Report.report_date.desc()).all()

    def create_report(self, data: dict) -> Report:
        report = Report(**data)
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        invalidate_stats_cache()
        return report

    def get_stats(self):
        return get_stats_cached()
