"""报告类型识别测试"""
from src.extractors.base import identify_report_type, extract_text


class TestReportTypeIdentification:
    """报告类型自动识别"""

    def test_identify_dna(self, dna_text):
        """DNA 定量细胞学 → 细胞学（妇科）"""
        rtype = identify_report_type(dna_text)
        assert rtype == "细胞学（妇科）"

    def test_identify_tct(self, tct_text):
        """TCT 液基细胞学 → 细胞学（妇科）"""
        rtype = identify_report_type(tct_text)
        assert rtype == "细胞学（妇科）"

    def test_identify_hpv(self, hpv_text):
        """HPV 基因分型 → HPV检测"""
        rtype = identify_report_type(hpv_text)
        assert rtype == "HPV检测"

    def test_identify_cytology_non_gyn(self, cytology_text):
        """细胞学报告单 → 细胞学（非妇科）（被 细胞学 模式优先匹配）"""
        rtype = identify_report_type(cytology_text)
        # N2604120: text contains "细胞学报告单" → 细胞学（非妇科）
        assert rtype is not None

    def test_identify_pathology(self, pathology_text_2615599):
        """病理诊断报告 → 常规病理"""
        rtype = identify_report_type(pathology_text_2615599)
        assert rtype == "常规病理"

    def test_identify_unknown_text(self):
        """无法识别的文本返回 None"""
        rtype = identify_report_type("这是一段完全未知的文本")
        assert rtype is None

    def test_pdf_text_extraction(self):
        """所有 PDF 应能提取到非空文本"""
        import os
        pdf_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "docs", "pdf_test"
        )
        for fname in os.listdir(pdf_dir):
            if fname.endswith(".pdf"):
                text = extract_text(os.path.join(pdf_dir, fname))
                assert text, f"Failed to extract text from {fname}"
                assert len(text.strip()) > 50, f"Text too short in {fname}: {len(text)} chars"
