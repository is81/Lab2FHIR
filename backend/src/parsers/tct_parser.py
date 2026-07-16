"""TCT液基细胞学报告解析器"""

import re


def parse_tct(text: str) -> tuple[dict, str]:
    """解析TCT报告，返回(结构化数据, 诊断结论)"""
    data = {}

    # 检验方法
    m = re.search(r'检验方法[：:]\s*(.+?)(?:\s|$)', text)
    if m:
        data["检验方法"] = m.group(1).strip()

    # 标本满意度
    m = re.search(r'标本满意度[：:]\s*(.+?)(?:\s|$)', text)
    if m:
        data["标本满意度"] = m.group(1).strip()

    # 炎症程度
    m = re.search(r'炎症程度[：:]\s*(.+?)(?:\s|$)', text)
    if m:
        data["炎症程度"] = m.group(1).strip()

    # 炎症细胞遮盖比率
    m = re.search(r'炎症细胞/遮盖比率[：:]\s*(.+?)(?:\s|$)', text)
    if m:
        data["炎症细胞遮盖比率"] = m.group(1).strip()

    # 细胞项目
    cell_items = {}
    cell_patterns = [
        (r'鳞状上皮细胞[：:]\s*(有|无)', '鳞状上皮细胞'),
        (r'颈管上皮细胞[：:]\s*(有|无)', '颈管上皮细胞'),
        (r'化生细胞[：:]\s*(有|无)', '化生细胞'),
        (r'萎缩反应[：:]\s*(有|无)', '萎缩反应'),
        (r'柱状上皮细胞[：:]\s*(有|无)', '柱状上皮细胞'),
        (r'子宫内膜细胞[：:]\s*(有|无)', '子宫内膜细胞'),
    ]
    for pat, name in cell_patterns:
        m = re.search(pat, text)
        if m:
            cell_items[name] = m.group(1)
    if cell_items:
        data["细胞项目"] = cell_items

    # 微生物项目
    micro_items = {}
    micro_patterns = [
        (r'滴虫感染[：:]\s*(有|无)', '滴虫感染'),
        (r'放线菌感染[：:]\s*(有|无)', '放线菌感染'),
        (r'霉菌感染[：:]\s*(有|无)', '霉菌感染'),
        (r'念珠菌感染[：:]\s*(有|无)', '念珠菌感染'),
        (r'线索细胞[：:]\s*(有|无)', '线索细胞'),
        (r'细菌过度增生[：:]\s*(有|无)', '细菌过度增生'),
        (r'球杆菌感染[：:]\s*(有|无)', '球杆菌感染'),
        (r'HPV感染表现[：:]\s*(有|无)', 'HPV感染表现'),
        (r'疱疹病毒感染依据[：:]\s*(有|无)', '疱疹病毒感染'),
    ]
    for pat, name in micro_patterns:
        m = re.search(pat, text)
        if m:
            micro_items[name] = m.group(1)
    if micro_items:
        data["微生物项目"] = micro_items

    # 诊断结论 - TCT的核心结果通常在 "无上皮内病变" 或 "NILM" 或 "ASC-US" 等
    diagnosis = ""
    for pat in [
        r'(无上皮内病变或恶性病变[^\n]*)',
        r'(非典型鳞状细胞[^\n]*)',
        r'(低[级别度]鳞状上皮内病变[^\n]*)',
        r'(高[级别度]鳞状上皮内病变[^\n]*)',
        r'(鳞状细胞癌[^\n]*)',
    ]:
        m = re.search(pat, text)
        if m:
            diagnosis = m.group(1).strip()
            break
    if not diagnosis:
        m = re.search(r'\b(NILM|ASC[- ]US|LSIL|HSIL|AGC|ASC[- ]H)\b', text)
        if m:
            diagnosis = m.group(1)

    return data, diagnosis
