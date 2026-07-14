"""PDF 转换 API（需 pathology_staff 角色）"""
import os
import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from ..config import get_settings
from ..db.models import Report
from ..db.repository import ReportRepository, get_db, PARSER_REGISTRY
from ..extractors.base import extract_text, identify_report_type
from ..parsers.patient_parser import parse_patient_info
from ..parsers.dna_parser import parse_dna
from ..parsers.tct_parser import parse_tct
from ..parsers.gastric_parser import parse_gastric
from ..parsers.pathology_parser import parse_pathology
from ..fhir.generator import generate_fhir_bundle
from ..auth.dependencies import require_role

_settings = get_settings()
logger = logging.getLogger("lab2fhir")

# 直接写日志文件（不依赖 logging 框架）
_LOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "lab2fhir.log"
)
def _log(msg):
    line = f"{datetime.now().isoformat()} [convert] {msg}\n"
    with open(_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)

router = APIRouter(tags=["convert"])

UPLOAD_DIR = _settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE = _settings.MAX_FILE_SIZE


@router.post("/convert")
async def convert_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["pathology_staff"]))
):
    """上传一份PDF，返回FHIR Bundle"""
    content = await file.read()

    # 修复 Windows GBK 编码导致的中文文件名乱码
    filename = file.filename or ""
    try:
        filename = filename.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass

    _log(f"RECV: {filename} ({len(content)} bytes)")

    if not filename or not filename.lower().endswith(".pdf"):
        _log(f"REJECT: not PDF {filename}")
        return {"success": False, "error": "仅支持PDF文件"}

    if len(content) > MAX_FILE_SIZE:
        _log(f"REJECT: too large {filename}")
        return {"success": False, "error": f"文件大小超过{MAX_FILE_SIZE // 1024 // 1024}MB限制"}

    safe_name = f"{uuid.uuid4().hex}.pdf"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    try:
        with open(file_path, "wb") as f:
            f.write(content)

        raw_text = extract_text(file_path)
        if not raw_text:
            _log(f"FAIL: empty text {filename}")
            os.remove(file_path)
            return {"success": False, "error": "无法从PDF中提取文本"}

        report_type = identify_report_type(raw_text) or identify_report_type(filename)
        _log(f"TYPE: {report_type} <- {filename}")

        patient = parse_patient_info(raw_text)

        if report_type == "细胞学（妇科）":
            if "DNA定量" in raw_text or "DNA倍体" in raw_text:
                parsed_data, diagnosis = parse_dna(raw_text)
            else:
                parsed_data, diagnosis = parse_tct(raw_text)
        elif report_type == "常规病理":
            if "H.P." in raw_text and "上皮内瘤变" in raw_text:
                parsed_data, diagnosis = parse_gastric(raw_text)
            elif "慢性炎症" in raw_text and "活动性" in raw_text:
                parsed_data, diagnosis = parse_gastric(raw_text)
            else:
                parsed_data, diagnosis = parse_pathology(raw_text)
        else:
            parser = PARSER_REGISTRY.get(report_type)
            if parser:
                parsed_data, diagnosis = parser(raw_text)
            else:
                _log(f"FAIL: no parser for {report_type} <- {filename}")
                parsed_data, diagnosis = {}, ""

        fhir_bundle = generate_fhir_bundle(
            pathology_id=patient.get("pathology_id", ""),
            patient_name=patient.get("patient_name", ""),
            gender=patient.get("gender", ""),
            age=patient.get("age"),
            report_type=report_type,
            report_date=patient.get("report_date"),
            diagnosis=diagnosis,
            parsed_data=parsed_data
        )

        repo = ReportRepository(db)
        pid = patient.get("pathology_id", "")

        if pid:
            existing = db.query(Report).filter(
                Report.pathology_id == pid,
                Report.report_type == report_type,
                Report.pdf_filename == filename
            ).first()
            if existing:
                _log(f"SKIP: duplicate {pid} ({report_type})")
                os.remove(file_path)
                return {
                    "success": False, "skipped": True,
                    "message": f"已存在：{pid} ({report_type})"
                }

        report = repo.create_report({
            "pathology_id": pid,
            "patient_name": patient.get("patient_name", ""),
            "gender": patient.get("gender", ""),
            "age": patient.get("age"),
            "report_type": report_type,
            "report_date": patient.get("report_date"),
            "sample_date": patient.get("sample_date"),
            "hospital": patient.get("hospital", ""),
            "department": patient.get("department", ""),
            "doctor": patient.get("doctor", ""),
            "diagnosis": diagnosis,
            "diagnosis_summary": diagnosis[:100] if diagnosis else "",
            "status": "completed",
            "raw_text": raw_text,
            "parsed_data": parsed_data,
            "fhir_bundle": fhir_bundle,
            "pdf_filename": filename,
            "pdf_path": file_path
        })

        _log(f"OK: {pid} ({report_type}) id={report.id}")
        return {
            "success": True,
            "report_id": report.id,
            "report_type": report_type,
            "patient_name": patient.get("patient_name"),
            "diagnosis": diagnosis,
            "fhir_bundle": fhir_bundle
        }
    except Exception as e:
        import traceback
        _log(f"ERROR: {filename} | {e}\n{traceback.format_exc()}")
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except OSError: pass
        return {"success": False, "error": str(e)}


@router.post("/convert/batch")
async def convert_batch(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["pathology_staff"]))
):
    results = []
    for f in files:
        try:
            result = await convert_pdf(f, db)
        except Exception as e:
            result = {"success": False, "error": str(e), "filename": f.filename}
        results.append(result)
    success = sum(1 for r in results if r.get("success"))
    return {"total": len(files), "success": success, "fail": len(files) - success, "results": results}


@router.delete("/admin/clear")
def clear_all_data(
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["pathology_staff"]))
):
    """清空数据库和上传文件（仅管理员）"""
    deleted_rows = db.query(Report).delete()
    db.commit()

    try:
        from sqlalchemy import text
        db.execute(text("DELETE FROM reports_fts"))
        db.commit()
    except Exception:
        pass  # FTS 表可能不存在

    upload_count = 0
    if os.path.isdir(UPLOAD_DIR):
        for fname in os.listdir(UPLOAD_DIR):
            if fname.endswith(".pdf"):
                os.remove(os.path.join(UPLOAD_DIR, fname))
                upload_count += 1

    _log(f"CLEAR: {deleted_rows} reports, {upload_count} files")
    return {"success": True, "reports_deleted": deleted_rows, "files_deleted": upload_count}
