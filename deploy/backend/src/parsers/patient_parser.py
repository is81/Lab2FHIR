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

    # 姓名（兼容 IHC 格式 "姓 名：" 含空格）
    m = re.search(r'姓\s*名[：:]\s*(.+?)(?:\s{2,}|\n|$)', text)
    if m:
        name = m.group(1).strip()
        for sep in ['性别', '年龄', '出生日期', '样本条码', '送检', '门诊号', '床号', '性 别']:
            idx = name.find(sep)
            if idx > 0:
                name = name[:idx].strip()
                break
        info["patient_name"] = name

    # 性别（兼容 IHC 格式 "性 别：" 含空格）
    m = re.search(r'性\s*别[：:]\s*(男|女)', text)
    if m:
        info["gender"] = m.group(1)

    # 年龄（兼容 IHC 格式 "年 龄：" 含空格）
    m = re.search(r'年\s*龄[：:]\s*(\d+)', text)
    if m:
        try:
            info["age"] = int(m.group(1))
        except ValueError:
            pass

    # 送检医院（容错截断）
    m = re.search(r'送检(?:单位|医院)[：:]\s*(.+?)(?:\s{2,}|\n|$)', text)
    if m:
        hosp = m.group(1).strip()
        for sep in ['送检科室', '送检科别', '送检医生', '送检医师', '标本类型', '患者电话', '门诊号', '床号', '样本条码', '病理号']:
            idx = hosp.find(sep)
            if idx > 0: hosp = hosp[:idx].strip()
        info["hospital"] = hosp
    elif not info.get("hospital"):
        m = re.search(r'(?:武警.*?医院|某市.*?医院)', text)
        if m:
            info["hospital"] = m.group(0)

    # 送检科室（兼容 IHC 格式 "送检科别："）
    m = re.search(r'送检(?:科室|科别)[：:]\s*(.+?)(?:\s{2,}|\n|$)', text)
    if m:
        dept = m.group(1).strip()
        field_labels = ['送检医生', '送检医师', '送检医院', '标本类型', '患者电话',
                        '门诊号', '门 诊 号', '床号', '床 号', '住院号', '住 院 号', '样本条码']
        if dept and any(dept.startswith(sep) for sep in field_labels):
            dept = ''
        else:
            for sep in field_labels:
                idx = dept.find(sep)
                if idx > 0:
                    dept = dept[:idx].strip()
                    break
        info["department"] = dept

    # 送检医生（兼容 IHC 格式 "送检医师："）
    m = re.search(r'送检(?:医生|医师)[：:]\s*(.+?)(?:\s{2,}|\n|$)', text)
    if m:
        doc = m.group(1).strip()
        for sep in ['标本类型', '门诊号', '住院号', '床号', '床 号', '患者电话',
                     '样本条码', '送检医院', '送检日期', '离体时间']:
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
