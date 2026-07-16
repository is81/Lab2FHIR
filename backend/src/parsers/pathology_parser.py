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

    # Unicode 引号常量
    lq = '“'  # "
    rq = '”'  # "
    lb = '「'  # 「
    rb = '」'  # 」

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

    # 策略1b：IHC免疫组化补充报告 → 提取检测结果
    if not diagnosis and data.get("免疫组化结果") or (
        not diagnosis and "免疫组化" in text and "检测结果" in text):
        # 提取 "检测结果：" 或 "免疫组化结果：" 之后到 "备注" 之前的内容
        m = re.search(r'(?:检测|免疫组化)结果[：:]\s*\n?(.+?)(?=\n\s*(?:备注|Signed|诊断医师|注：))', text, re.DOTALL)
        if m:
            ihc_text = m.group(1).strip()
            # 清理：每行一条 IHC 指标
            lines = [l.strip() for l in ihc_text.split('\n') if l.strip() and len(l.strip()) > 5]
            if lines:
                diagnosis = '\n'.join(lines)

    # 策略2：短篇报告 → 提取带引号的部位诊断
    if not diagnosis:
        diagnoses = []
        for pat in [f'[{lq}\\"]([^{rq}\\"]+)[{rq}\\]"]\\s*([^{lq}{lb}\\n]+)',
                     f'{lb}([^{rb}]+){rb}\\s*([^{lb}\\n]+)']:
            for m in re.finditer(pat, text):
                site = m.group(1)
                desc = m.group(2)
                # 取材描述以 ：开头（如 "部位"：灰白组织），诊断则直接跟文本
                if desc.strip().startswith('：') or desc.strip().startswith(':'):
                    continue
                # 处理跨行续行：诊断可能被换行截断，合并下一行
                end_pos = m.end()
                remaining = text[end_pos:]
                next_lines = remaining.split('\n')
                for nl in next_lines:
                    nl = nl.strip()
                    if not nl:
                        continue
                    # 续行终止条件：新部位、新章节
                    if any(nl.startswith(c) for c in [lq, rq, lb]):
                        break
                    if any(kw in nl for kw in ['备注', 'Signed', '诊断医师',
                                                  '审核医师', '免疫组化', '接收时间']):
                        break
                    if nl.startswith('：') or nl.startswith(':'):
                        break
                    # 取材描述续行（以数字+cm/× 开头）
                    if nl[0].isdigit() and ('cm' in nl or '×' in nl):
                        break
                    desc += nl
                diagnoses.append(f'{lq}{site}{rq}{desc}')
        if diagnoses:
            diagnosis = "\n".join(diagnoses)

    # 策略3：兜底 — 提取"备注"或"Signed*-Report"之前的非元数据行
    if not diagnosis:
        lines = text.split('\n')
        capture = False
        in_specimen = False  # 追踪是否在取材描述区域内
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
            # 跳过取材描述行
            if any(kw in line for kw in ['送检为', '福尔马林', '包装外附', '术式:', '标本长度', '肿瘤距']):
                in_specimen = True
                continue
            # 取材描述续行：以数字+cm/× 或颜色描述开头
            if in_specimen:
                if (line[0].isdigit() and ('cm' in line or '×' in line)) or \
                   any(line.startswith(w) for w in ['灰白', '灰红', '灰黄', '灰褐', '涂', '切面', '全取']):
                    continue
                in_specimen = False
            # 取材描述行（"部位"：...）vs 诊断行（"部位"直接诊断）
            if line.startswith(lq) or line.startswith('"') or line.startswith(lb):
                m = re.match(f'[{lq}\\"{lb}]([^{rq}\\"{rb}]+)[{rq}\\"{rb}]\\s*[：:]', line)
                if m:
                    in_specimen = True
                    continue
            if line and len(line) > 5:
                diag_lines.append(line)
        if diag_lines:
            diagnosis = "；".join(diag_lines)

    diagnosis = diagnosis.strip()

    return data, diagnosis
