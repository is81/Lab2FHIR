"""细胞学报告解析器（穿刺/脱落细胞学）"""

import re


def parse_cytology(text: str) -> tuple[dict, str]:
    """解析细胞学报告，返回(结构化数据, 诊断结论)"""
    data = {}

    # 标本类型
    m = re.search(r'标本类型[：:]\s*(.+?)(?:\s|$)', text)
    if m:
        data["标本类型"] = m.group(1)

    # 诊断结论：临床病史/诊断之后到备注之前的核心描述
    diagnosis = ""

    # 方法1：找标本描述后面带引号的关键诊断
    # "取样部位，方法" + 镜下所见 + 诊断结论
    m = re.search(r'[「""]([^「」""]+?)[」""]\s*镜下见(.+?)(?:。|$)', text)
    if m:
        specimen = m.group(1)
        finding = m.group(2).strip()
        data["送检标本"] = specimen
        diagnosis = f"{specimen}：镜下见{finding}"

    # 方法2：如果上面没匹配到，找 临床病史/诊断 后的内容
    if not diagnosis:
        m = re.search(r'临床病史/诊断[：:]?\s*\n?(.+?)(?:备注|$)', text, re.DOTALL)
        if m:
            content = m.group(1).strip()
            # 去掉取材描述，保留诊断部分
            # 通常诊断在最后一句
            lines = content.split('\n')
            diagnosis_lines = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # 跳过取材描述
                if any(kw in line for kw in ['送检为', '福尔马林', '包装外附']):
                    continue
                diagnosis_lines.append(line)
            diagnosis = '\n'.join(diagnosis_lines)

    # 方法3：找包含"考虑为"、"符合"、"考虑"的诊断句
    if not diagnosis or len(diagnosis) < 10:
        for pat in [
            r'(考虑为[^。\n]+[。])',
            r'(符合[^。\n]+[。])',
            r'(镜下见[^。\n]+[。])',
        ]:
            m = re.search(pat, text)
            if m:
                diagnosis = m.group(1)
                break

    diagnosis = diagnosis.strip()

    return data, diagnosis
