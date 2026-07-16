"""胃镜病理报告解析器"""

import re


def parse_gastric(text: str) -> tuple[dict, str]:
    """解析胃镜病理报告，返回(结构化数据, 诊断结论)"""
    data = {}

    # 标本部位
    m = re.search(r'取样部位为[「""](.+?)[」""]', text)
    if m:
        data["取样部位"] = m.group(1)

    # 评分表格行
    m = re.search(r'(\S+)\s+(\S+)\s+([+\-/]+)\s+([+\-/]+)\s+([+\-/]+)\s+([+\-/]+)\s+([+\-/]+)\s+([+\-/]+)', text)
    if m:
        data["评分"] = {
            "部位": m.group(1),
            "黏膜": m.group(2),
            "慢性炎症": m.group(3),
            "活动性": m.group(4),
            "萎缩": m.group(5),
            "肠上皮化生": m.group(6),
            "上皮内瘤变": m.group(7),
            "H.P.": m.group(8)
        }

    # 诊断结论：评分表后的带引号诊断行
    diagnosis = ""
    # 匹配 "部位"诊断文本。 格式
    for pat in [
        r'[“”]([^””]+)[“”]\s*([^”「\n]+)',
        r'「([^」]+)」\s*([^「\n]+)',
    ]:
        matches = re.findall(pat, text)
        if matches:
            diagnoses = []
            for site, desc in matches:
                # 过滤掉非诊断内容（如取材描述、标本类型等）
                if any(kw in site + desc for kw in ['福尔马林', '送检为', '包装外附',
                    '全取', '灰白', '灰红', '大小', '直径', '切缘', '涂墨', '系线', 'cm']):
                    continue
                diagnoses.append(f"“{site}”{desc}")
            if diagnoses:
                diagnosis = "\n".join(diagnoses)
                break

    # 如果没匹配到引号格式，尝试取评分表后的最后一句
    if not diagnosis:
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'H.P.' in line and '/' in line:
                # 下一行或下下行通常是诊断
                for j in range(i+1, min(i+4, len(lines))):
                    candidate = lines[j].strip()
                    if candidate and len(candidate) > 5 and '备注' not in candidate:
                        diagnosis = candidate
                        break
                break

    # 清理诊断中的引号
    diagnosis = diagnosis.strip().strip('"').strip('"').strip()

    return data, diagnosis
