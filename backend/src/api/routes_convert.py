"""PDF 转换 API（需 pathology_staff 角色）"""
import os
import uuid
import logging
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
logger = logging.getLogger("lab2fhir.convert")
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
    logger.info(f"收到文件: {file.filename} ({len(content)} 字节)")

    # 1.2 修复：文件类型和大小校验
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        logger.warning(f"非PDF文件被拒: {file.filename}")
        return {"success": False, "error": "仅支持PDF文件"}

    if len(content) > MAX_FILE_SIZE:
        logger.warning(f"文件过大被拒: {file.filename} ({len(content)} 字节)")
        return {"success": False, "error": f"文件大小超过{MAX_FILE_SIZE // 1024 // 1024}MB限制"}

    # 1.2 修复：使用 UUID 文件名防止路径遍历
    safe_name = f"{uuid.uuid4().hex}.pdf"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    try:
        with open(file_path, "wb") as f:
            f.write(content)

        raw_text = extract_text(file_path)
        if not raw_text:
            # 1.3 修复：失败时清理文件
            logger.warning(f"文本提取为空: {file.filename}")
            os.remove(file_path)
            return {"success": False, "error": "无法从PDF中提取文本"}

        report_type = identify_report_type(raw_text) or identify_report_type(file.filename)
        logger.info(f"识别类型: {report_type} (文件: {file.filename})")

        patient = parse_patient_info(raw_text)

        # 解析器调度
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
                logger.warning(f"无解析器: {report_type} ({file.filename})")
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

        # 去重：同一 (病理号, 类型, 文件名) 才跳过（DNA+TCT同pid不同类型需保留）
        if pid:
            existing = db.query(Report).filter(
                Report.pathology_id == pid,
                Report.report_type == report_type,
                Report.pdf_filename == file.filename
            ).first()
            if existing:
                logger.info(f"跳过重复: {pid} ({report_type})")
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
            "pdf_filename": file.filename,  # 原始文件名仅作为元数据
            "pdf_path": file_path
        })

        logger.info(f"导入成功: {pid} ({report_type}) report_id={report.id}")
        return {
            "success": True,
            "report_id": report.id,
            "report_type": report_type,
            "patient_name": patient.get("patient_name"),
            "diagnosis": diagnosis,
            "fhir_bundle": fhir_bundle
        }
    except Exception as e:
        logger.error(f"Convert failed [{file.filename}]: {e}", exc_info=True)
        # 1.3 修复：异常时清理临时文件
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        return {"success": False, "error": str(e)}


@router.post("/convert/batch")
async def convert_batch(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["pathology_staff"]))
):
    """批量上传PDF"""
    results = []
    for file in files:
        try:
            result = await convert_pdf(file, db)
        except Exception as e:
            result = {"success": False, "error": str(e), "filename": file.filename}
        results.append(result)
    success = sum(1 for r in results if r.get("success"))
    return {"total": len(files), "success": success, "fail": len(files) - success, "results": results}
