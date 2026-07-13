"""HPV基因分型报告解析器"""

import re


def parse_hpv(text: str) -> tuple[dict, str]:
    """解析HPV报告，返回(结构化数据, 诊断结论)"""
    data = {}

    # 标本质量
    m = re.search(r'标本质量[：:]\s*(.+?)(?:\s|$)', text)
    if m:
        data["标本质量"] = m.group(1).strip()

    # 标本类型
    m = re.search(r'标本类型[：:]\s*(.+?)(?:\s|$)', text)
    if m:
        data["标本类型"] = m.group(1).strip()

    # 检测方法
    m = re.search(r'检测方法[：:]\s*(.+?)(?:\s|$)', text)
    if m:
        data["检测方法"] = m.group(1).strip()

    # 高危型HPV结果
    m = re.search(r'高危型HPV[：:]\s*(阴性|阳性)(?:[-—]\s*(\S+))?', text)
    if m:
        data["高危型HPV"] = m.group(1)
        if m.group(2):
            data["高危型HPV分型"] = m.group(2)

    # 低危型HPV结果
    m = re.search(r'低危型HPV[：:]\s*(阴性|阳性)(?:[-—]\s*(\S+))?', text)
    if m:
        data["低危型HPV"] = m.group(1)
        if m.group(2):
            data["低危型HPV分型"] = m.group(2)

    # 提取具体HPV分型
    subtypes = []
    for m in re.finditer(r'HPV[- ]?(\d+)', text):
        subtype = f"HPV{m.group(1)}"
        if subtype not in subtypes:
            subtypes.append(subtype)
    if subtypes:
        data["具体分型"] = subtypes

    # 诊断结论
    lines = []
    if data.get("高危型HPV"):
        lines.append(f"高危型HPV：{data['高危型HPV']}")
        if data.get("高危型HPV分型"):
            lines[-1] += f"-{data['高危型HPV分型']}"
    if data.get("低危型HPV"):
        lines.append(f"低危型HPV：{data['低危型HPV']}")
        if data.get("低危型HPV分型"):
            lines[-1] += f"-{data['低危型HPV分型']}"

    diagnosis = "\n".join(lines)

    return data, diagnosis
