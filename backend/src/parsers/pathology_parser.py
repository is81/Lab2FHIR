"""病理诊断报告解析器"""

import re


def parse_pathology(text: str) -> tuple[dict, str]:
    """解析病理诊断报告，返回(结构化数据, 诊断结论)"""
    data = {}

    # 提取结构化字段（长篇报告）
    structured_fields = {
        "术式": r'术式[：:]\s*(.+?)(?:\s|$)',
        "标本长度": r'标本长度[：:]\s*(.+?)(?:\s|$)',
        "肿瘤大小": r'肿瘤大小[：:]\s*(.+?)(?:\s|$)',
        "组织学类型": r'组织学类型[：:]\s*(.+?)(?:\s|$)',
        "组织学分级": r'组织学分级[：:]\s*(.+?)(?:\s|$)',
        "病理分期": r'病理分期[：:]\s*(.+?)(?:\s|$)',
        "肿瘤累及范围": r'肿瘤累及范围[：:]\s*(.+?)(?:\s|$)',
        "脉管浸润": r'脉管浸润[：:]\s*(.+?)(?:\s|$)',
        "神经浸润": r'神经浸润[：:]\s*(.+?)(?:\s|$)',
        "区域淋巴结": r'区域淋巴结[：:]\s*(.+?)(?:\s|$)',
        "免疫组化结果": r'免疫组化结果[：:]\s*(.+?)(?:\s|$)',
    }

    for key, pat in structured_fields.items():
        m = re.search(pat, text)
        if m:
            data[key] = m.group(1).strip()

    # 提取切缘信息
    margins = {}
    for pat, label in [
        (r'一侧切缘[：:]\s*(.+?)(?:\s|$)', '一侧切缘'),
        (r'另一侧切缘[：:]\s*(.+?)(?:\s|$)', '另一侧切缘'),
        (r'另送(\S+)切缘[：:]\s*(.+?)(?:\s|$)', None),  # 动态key
    ]:
        m = re.search(pat, text)
        if m:
            if label:
                margins[label] = m.group(1).strip()
            else:
                margins[f"{m.group(1)}切缘"] = m.group(2).strip()
    if margins:
        data["切缘"] = margins

    # ===== 诊断结论 =====
    diagnosis = ""

    # 策略1：长篇报告 → 用结构化字段拼接
    if data.get("组织学类型"):
        parts = []
        for key in ["组织学类型", "组织学分级", "病理分期"]:
            if data.get(key):
                parts.append(f"{key}：{data[key]}")
        if parts:
            diagnosis = "\n".join(parts)

    # 策略2：短篇报告 → 提取带引号的部位诊断
    if not diagnosis:
        diagnoses = []
        # 匹配 ASCII 直引号 "、"、Unicode 弯引号 “”、中文引号 「」
        for pat in [r'[“\"]([^”\"]+)[”\"]\s*([^。\n]+。?)',
                     r'「([^」]+)」\s*([^。\n]+。?)']:
            matches = re.findall(pat, text)
            for site, desc in matches:
                # 过滤取材描述（含尺寸、颜色、切缘等测量描述的行）
                skip_kw = ['福尔马林', '送检为', '包装外附', '全取',
                          '灰白', '灰红', '灰褐', '灰黄', '覆皮',
                          '大小', '直径', '切缘', '涂墨', '系线',
                          'cm', '×', '保留', '切面']
                if any(kw in site + desc for kw in skip_kw):
                    continue
                diagnoses.append(f"“{site}”{desc}")
        if diagnoses:
            diagnosis = "\n".join(diagnoses)

    # 策略3：兜底 — 提取"备注"或"Signed*-Report"之前的非元数据行
    if not diagnosis:
        lines = text.split('\n')
        # 找到第一个诊断行（在"临床病史"之后，"备注"之前）
        capture = False
        diag_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if '临床病史' in line:
                capture = True
                continue
            if not capture:
                continue
            if any(kw in line for kw in ['备注', 'Signed*-Report', '诊断医师', '审核医师', '接收时间']):
                break
            # 跳过元数据行
            if any(kw in line for kw in ['送检为', '福尔马林', '包装外附', '术式:', '标本长度', '肿瘤距']):
                continue
            if line and len(line) > 5:
                diag_lines.append(line)
        if diag_lines:
            diagnosis = "；".join(diag_lines)

    diagnosis = diagnosis.strip()

    return data, diagnosis
