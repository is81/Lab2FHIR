"""通用患者信息解析"""

import re
from datetime import datetime


def parse_patient_info(text: str) -> dict:
    """从报告文本中提取患者基本信息"""
    info = {}

    # 病理号
    m = re.search(r'[病理条码]号[：:]?\s*([A-Z]?\d+)', text)
    if m:
        info["pathology_id"] = m.group(1)

    # 姓名（2.3 修复：允许空格；容错：截断到下一个字段标签之前）
    m = re.search(r'姓名[：:]\s*(.+?)(?:\s{2,}|\n|$)', text)
    if m:
        name = m.group(1).strip()
        # 脱敏/OCR可能导致后续字段连在一起，截断到第一个已知字段标签
        for sep in ['性别', '年龄', '出生日期', '样本条码', '送检', '门诊号', '床号']:
            idx = name.find(sep)
            if idx > 0:
                name = name[:idx].strip()
                break
        info["patient_name"] = name

    # 性别
    m = re.search(r'性别[：:]\s*(男|女)', text)
    if m:
        info["gender"] = m.group(1)

    # 年龄
    m = re.search(r'年龄[：:]\s*(\d+)', text)
    if m:
        try:
            info["age"] = int(m.group(1))
        except ValueError:
            pass

    # 送检医院（容错截断）
    m = re.search(r'送检(?:单位|医院)[：:]\s*(.+?)(?:\s{2,}|\n|$)', text)
    if m:
        hosp = m.group(1).strip()
        for sep in ['送检科室', '送检医生', '标本类型', '患者电话', '门诊号', '床号', '样本条码']:
            idx = hosp.find(sep)
            if idx > 0: hosp = hosp[:idx].strip()
        info["hospital"] = hosp
    elif not info.get("hospital"):
        m = re.search(r'(?:武警.*?医院|某市.*?医院)', text)
        if m:
            info["hospital"] = m.group(0)

    # 送检科室（容错截断）
    m = re.search(r'送检科室[：:]\s*(.+?)(?:\s{2,}|\n|$)', text)
    if m:
        dept = m.group(1).strip()
        for sep in ['送检医生', '送检医院', '标本类型', '患者电话', '门诊号', '床号', '样本条码']:
            idx = dept.find(sep)
            if idx > 0: dept = dept[:idx].strip()
        info["department"] = dept

    # 送检医生（容错截断）
    m = re.search(r'送检医生[：:]\s*(.+?)(?:\s{2,}|\n|$)', text)
    if m:
        doc = m.group(1).strip()
        for sep in ['标本类型', '门诊号', '住院号', '床号', '患者电话', '样本条码', '送检医院']:
            idx = doc.find(sep)
            if idx > 0: doc = doc[:idx].strip()
        info["doctor"] = doc

    # 报告日期
    m = re.search(r'报告(?:日期|时间)[：:]\s*(\d{4}-\d{2}-\d{2})', text)
    if m:
        date_str = m.group(1)
        try:
            info["report_date"] = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            info["report_date"] = date_str

    # 采集/采样日期
    m = re.search(r'(?:采集|离体|取材)时间[：:]\s*(\d{4}-\d{2}-\d{2})', text)
    if m:
        date_str = m.group(1)
        try:
            info["sample_date"] = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            info["sample_date"] = date_str

    # 标本类型
    m = re.search(r'标本类型[：:]\s*(.+?)(?:\s|$)', text)
    if m:
        info["specimen_type"] = m.group(1).strip()

    return info
