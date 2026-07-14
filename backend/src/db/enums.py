"""6.3 修复：报告类型枚举，消除硬编码字符串散布"""
from enum import Enum


class ReportType(str, Enum):
    """报告类型枚举"""
    CYTOLOGY_GYN = "细胞学（妇科）"
    HPV = "HPV检测"
    CYTOLOGY_NON_GYN = "细胞学（非妇科）"
    PATHOLOGY = "常规病理"


# LOINC 编码映射
LOINC_CODES: dict[str, str] = {
    ReportType.CYTOLOGY_GYN: "47527-7",
    ReportType.HPV: "21440-3",
    ReportType.CYTOLOGY_NON_GYN: "47527-7",
    ReportType.PATHOLOGY: "60568-3",
}

# LOINC 展示名称
LOINC_DISPLAYS: dict[str, str] = {
    ReportType.CYTOLOGY_GYN: "Cytology report (gynecologic)",
    ReportType.HPV: "HPV DNA test",
    ReportType.CYTOLOGY_NON_GYN: "Cytology report (non-gynecologic)",
    ReportType.PATHOLOGY: "Surgical pathology report",
}

# 类型标签映射
TYPE_LABELS: dict[str, str] = {
    v: v for v in [
        ReportType.CYTOLOGY_GYN,
        ReportType.HPV,
        ReportType.CYTOLOGY_NON_GYN,
        ReportType.PATHOLOGY,
    ]
}
