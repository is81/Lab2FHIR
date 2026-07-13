"""PDF文本提取基类"""
import os
import pdfplumber


def extract_text(file_path: str) -> str:
    """从PDF中提取全部文本"""
    if not os.path.exists(file_path):
        return ""
    try:
        with pdfplumber.open(file_path) as pdf:
            texts = []
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texts.append(t)
            return "\n".join(texts)
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""


def extract_text_with_positions(file_path: str) -> list:
    """提取带坐标的单词列表"""
    if not os.path.exists(file_path):
        return []
    with pdfplumber.open(file_path) as pdf:
        words = []
        for page in pdf.pages:
            words.extend(page.extract_words())
        return words


def identify_report_type(text: str) -> str | None:
    """根据文本内容识别报告类型"""
    if not text:
        return None

    # DNA/TCT → 细胞学（妇科）
    if "DNA定量细胞学检查报告" in text or "DNA倍体" in text:
        return "细胞学（妇科）"
    if "液基薄层细胞学检测报告" in text:
        return "细胞学（妇科）"

    # HPV
    if "人乳头状瘤病毒" in text:
        return "HPV检测"

    # 细胞学（非妇科）：N-series，标题为"细胞学报告单"
    if "细胞学报告单" in text:
        return "细胞学（非妇科）"

    # 胃镜/病理诊断 → 常规病理（胃镜，有独特评分表头）
    if "慢性炎症" in text and "活动性" in text and ("萎缩" in text or "肠上皮化生" in text):
        return "常规病理"
    if "H.P." in text and "上皮内瘤变" in text:
        return "常规病理"

    # 病理诊断报告（含补充、冰冻石蜡等变体）→ 常规病理
    if "病理诊断" in text and "报告单" in text:
        return "常规病理"

    return None


def identify_report_type_by_filename(filename: str) -> str | None:
    """根据文件名识别报告类型（ASCII-safe）"""
    name = os.path.basename(filename)
    if "DNA" in name or "TCT" in name:
        return "细胞学（妇科）"
    if "HPV" in name:
        return "HPV检测"

    import re
    if "胃镜" in name or "θ" in name:
        return "常规病理"

    return None
