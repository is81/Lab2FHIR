"""报告 CRUD + PDF 文件服务"""
import os
import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from ..config import get_settings
from ..db.repository import ReportRepository, get_db, TYPE_LABELS
from ..auth.dependencies import require_role

_settings = get_settings()
logger = logging.getLogger("lab2fhir.reports")
router = APIRouter(tags=["reports"])

PDF_TEST_DIR = _settings.PDF_TEST_DIR
_REAL_PDF_TEST_DIR = os.path.realpath(PDF_TEST_DIR)


def _serialize(r, full: bool = False):
    """6.1 修复：统一序列化函数"""
    base = {
        "id": r.id, "pathology_id": r.pathology_id,
        "patient_name": r.patient_name, "gender": r.gender, "age": r.age,
        "report_type": r.report_type,
        "report_type_label": TYPE_LABELS.get(r.report_type, r.report_type or ""),
        "hospital": r.hospital, "department": r.department, "doctor": r.doctor,
        "report_date": str(r.report_date) if r.report_date else None,
        "sample_date": str(r.sample_date) if r.sample_date else None,
        "diagnosis": r.diagnosis, "diagnosis_summary": r.diagnosis_summary,
        "status": r.status, "pdf_filename": r.pdf_filename,
        "created_at": str(r.created_at) if r.created_at else None,
    }
    if full:
        base["parsed_data"] = r.parsed_data
        base["fhir_bundle"] = r.fhir_bundle
        base["pdf_path"] = r.pdf_path
    return base


def _safe_pdf_path(filename: str) -> str | None:
    """1.6 修复：安全获取 PDF 路径（防路径遍历）"""
    safe = os.path.basename(filename)
    full = os.path.realpath(os.path.join(PDF_TEST_DIR, safe))
    if full.startswith(_REAL_PDF_TEST_DIR) and os.path.exists(full):
        return full
    return None


def _find_pdf_by_pid(pathology_id: str) -> str | None:
    """按病理号在 pdf_test 目录查找文件"""
    if not pathology_id:
        return None
    for fname in os.listdir(PDF_TEST_DIR):
        if pathology_id in fname and fname.lower().endswith(".pdf"):
            return os.path.join(PDF_TEST_DIR, fname)
    return None


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    return ReportRepository(db).get_stats()


class DeleteRequest(BaseModel):
    ids: list[int]

    @field_validator("ids")
    @classmethod
    def check_ids(cls, v):
        if not v or len(v) < 1:
            raise ValueError("至少选择一个报告")
        if len(v) > 200:
            raise ValueError("一次最多删除 200 条")
        return v


@router.delete("/reports")
def delete_reports(
    req: DeleteRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["pathology_staff"]))
):
    """批量删除报告（仅病理科管理员）"""
    repo = ReportRepository(db)
    deleted = repo.delete_reports(req.ids)
    return {"success": True, "deleted": deleted}


@router.get("/reports")
def list_reports(
    search: str = Query(None),
    report_type: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    repo = ReportRepository(db)
    result = repo.list_reports(search=search, report_type=report_type,
                               date_from=date_from, date_to=date_to,
                               page=page, page_size=page_size)
    return {
        "items": [_serialize(r) for r in result["items"]],
        "total": result["total"], "page": result["page"], "page_size": result["page_size"]
    }


@router.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    repo = ReportRepository(db)
    report = repo.get_report(report_id)
    if not report:
        # 4.6 修复：使用 HTTPException
        raise HTTPException(status_code=404, detail="报告不存在")
    return _serialize(report, full=True)


@router.get("/patients/{patient_name}/reports")
def get_patient_reports(patient_name: str, db: Session = Depends(get_db)):
    repo = ReportRepository(db)
    reports = repo.get_patient_reports(patient_name)
    return [_serialize(r) for r in reports]


@router.get("/reports/{report_id}/pdf")
def get_report_pdf(
    report_id: int,
    pid: str = Query(None),
    inline: bool = Query(False),
    db: Session = Depends(get_db)
):
    """返回报告的原始PDF文件。inline=1 时浏览器内联预览，否则触发下载。"""
    repo = ReportRepository(db)
    report = repo.get_report(report_id)
    disposition = "inline" if inline else "attachment"

    if report:
        # 1) 优先返回上传存储的 PDF（pdf_path 记录实际存储位置）
        if report.pdf_path and os.path.isfile(report.pdf_path):
            filename = report.pdf_filename or os.path.basename(report.pdf_path)
            return FileResponse(report.pdf_path, media_type="application/pdf",
                              filename=filename, content_disposition_type=disposition)

    # 2) 按数据库记录的文件名在 pdf_test 目录匹配
    if report and report.pdf_filename:
        safe = _safe_pdf_path(report.pdf_filename)
        if safe:
            return FileResponse(safe, media_type="application/pdf",
                              filename=report.pdf_filename, content_disposition_type=disposition)

    # 3) 按病理号在 pdf_test 目录查找
    pathology_id = pid or (report.pathology_id if report else None)
    if pathology_id:
        found = _find_pdf_by_pid(pathology_id)
        if found:
            return FileResponse(found, media_type="application/pdf",
                              content_disposition_type=disposition)

    raise HTTPException(status_code=404, detail="PDF文件未找到")


@router.get("/pdf/{filename:path}")
def serve_pdf_by_filename(filename: str):
    """按文件名提供PDF（1.6 修复：path 参数添加路径遍历防护）"""
    safe = os.path.basename(filename)
    full = os.path.realpath(os.path.join(PDF_TEST_DIR, safe))
    if not full.startswith(_REAL_PDF_TEST_DIR):
        raise HTTPException(status_code=403, detail="禁止访问")
    if not os.path.exists(full):
        raise HTTPException(status_code=404, detail="PDF文件未找到")
    return FileResponse(full, media_type="application/pdf", filename=safe)
