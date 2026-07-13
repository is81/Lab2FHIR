"""DNA倍体报告解析器"""

import re


def parse_dna(text: str) -> tuple[dict, str]:
    """解析DNA倍体报告，返回(结构化数据, 诊断结论)"""
    data = {}

    # 标本类型
    m = re.search(r'标本类型[：:]\s*(.+?)(?:\s|$)', text)
    if m:
        data["标本类型"] = m.group(1).strip()

    # 细胞总数
    m = re.search(r'细胞总数[：:]\s*(\d+)', text)
    if m:
        data["细胞总数"] = int(m.group(1))

    # DNA分析表格数据
    table = []
    # 二倍体
    m = re.search(r'二倍体\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', text)
    if m:
        try:
            table.append({"类别": "二倍体", "Percent": float(m.group(1)), "DI均值": float(m.group(2)), "STD": float(m.group(3))})
        except ValueError: pass

    # 非整倍体
    m = re.search(r'非整倍体\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', text)
    if m:
        try:
            table.append({"类别": "非整倍体", "Percent": float(m.group(1)), "DI均值": float(m.group(2)), "STD": float(m.group(3))})
        except ValueError: pass

    # 四倍体
    m = re.search(r'四倍体\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', text)
    if m:
        try:
            table.append({"类别": "四倍体", "Percent": float(m.group(1)), "DI均值": float(m.group(2)), "STD": float(m.group(3))})
        except ValueError: pass

    # 高倍体
    m = re.search(r'高倍体\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', text)
    if m:
        try:
            table.append({"类别": "高倍体", "Percent": float(m.group(1)), "DI均值": float(m.group(2)), "STD": float(m.group(3))})
        except ValueError: pass

    if table:
        data["DNA分析表格"] = table

    # 诊断结论
    diagnosis = ""
    # DNA检测结果后到报告说明前的内容
    m = re.search(r'DNA检测结果[：:]?\s*\n?(.+?)(?:报告说明|$)', text, re.DOTALL)
    if m:
        diagnosis = m.group(1).strip()

    return data, diagnosis
