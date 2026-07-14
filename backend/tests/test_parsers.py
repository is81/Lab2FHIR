"""解析器测试：DNA / TCT / HPV / 细胞学 / 病理诊断"""
from src.parsers.dna_parser import parse_dna
from src.parsers.tct_parser import parse_tct
from src.parsers.hpv_parser import parse_hpv
from src.parsers.cytology_parser import parse_cytology
from src.parsers.gastric_parser import parse_gastric
from src.parsers.pathology_parser import parse_pathology


class TestDnaParser:
    """DNA 倍体报告解析"""

    def test_parse_dna_returns_data_and_diagnosis(self, dna_text):
        parsed, diagnosis = parse_dna(dna_text)
        assert isinstance(parsed, dict)
        assert isinstance(diagnosis, str)

    def test_parse_dna_diagnosis(self, dna_text):
        _, diagnosis = parse_dna(dna_text)
        assert "未见DNA倍体异常细胞" in diagnosis

    def test_parse_dna_has_di_table(self, dna_text):
        parsed, _ = parse_dna(dna_text)
        assert "DNA分析表格" in parsed
        assert len(parsed["DNA分析表格"]) == 4  # 二倍体/非整倍体/四倍体/高倍体
        assert parsed["细胞总数"] == 6687

    def test_parse_dna_empty_text(self):
        parsed, diagnosis = parse_dna("")
        assert isinstance(parsed, dict)
        assert diagnosis == ""


class TestTctParser:
    """TCT 液基细胞学报告解析"""

    def test_parse_tct_returns_data_and_diagnosis(self, tct_text):
        parsed, diagnosis = parse_tct(tct_text)
        assert isinstance(parsed, dict)
        assert isinstance(diagnosis, str)

    def test_parse_tct_diagnosis(self, tct_text):
        _, diagnosis = parse_tct(tct_text)
        assert "NILM" in diagnosis or "无上皮内病变" in diagnosis

    def test_parse_tct_has_satisfaction(self, tct_text):
        parsed, _ = parse_tct(tct_text)
        assert parsed.get("标本满意度") == "满意"
        assert parsed.get("检验方法") == "薄层细胞检验"

    def test_parse_tct_has_cell_projects(self, tct_text):
        parsed, _ = parse_tct(tct_text)
        assert "细胞项目" in parsed
        assert isinstance(parsed["细胞项目"], dict)

    def test_parse_tct_has_microbe_projects(self, tct_text):
        parsed, _ = parse_tct(tct_text)
        assert "微生物项目" in parsed
        assert "滴虫感染" in parsed["微生物项目"]

    def test_parse_tct_empty_text(self):
        parsed, diagnosis = parse_tct("")
        assert isinstance(parsed, dict)
        assert diagnosis == ""


class TestHpvParser:
    """HPV 基因分型报告解析"""

    def test_parse_hpv_returns_data_and_diagnosis(self, hpv_text):
        parsed, diagnosis = parse_hpv(hpv_text)
        assert isinstance(parsed, dict)
        assert isinstance(diagnosis, str)

    def test_parse_hpv_has_genotypes(self, hpv_text):
        parsed, _ = parse_hpv(hpv_text)
        assert "高危型HPV" in parsed
        assert parsed["高危型HPV"] == "阴性"
        assert "低危型HPV" in parsed

    def test_parse_hpv_has_specific_genotype(self, hpv_text):
        parsed, _ = parse_hpv(hpv_text)
        assert "HPV54" in parsed.get("具体分型", [])

    def test_parse_hpv_empty_text(self):
        parsed, diagnosis = parse_hpv("")
        assert isinstance(parsed, dict)
        assert diagnosis == ""


class TestCytologyParser:
    """细胞学（非妇科）报告解析"""

    def test_parse_cytology_returns_data_and_diagnosis(self, cytology_text):
        parsed, diagnosis = parse_cytology(cytology_text)
        assert isinstance(parsed, dict)
        assert isinstance(diagnosis, str)

    def test_parse_cytology_diagnosis_contains_malignant(self, cytology_text):
        _, diagnosis = parse_cytology(cytology_text)
        # N2604120 诊断含"恶性肿瘤"
        assert "恶性肿瘤" in diagnosis or "肿瘤" in diagnosis

    def test_parse_cytology_empty_text(self):
        parsed, diagnosis = parse_cytology("")
        assert isinstance(parsed, dict)
        assert diagnosis == ""


class TestPathologyParser:
    """常规病理报告解析（胃镜 + 病理诊断）"""

    def test_parse_gastric_detects_gastric(self, pathology_text_2615599):
        """胃镜特征文本 → parse_gastric 应可处理"""
        parsed, diagnosis = parse_gastric(pathology_text_2615599)
        assert isinstance(parsed, dict)
        assert isinstance(diagnosis, str)

    def test_parse_pathology_2615599(self, pathology_text_2615599):
        """病理诊断解析 - 2615599（含丰富结构化字段）"""
        parsed, diagnosis = parse_pathology(pathology_text_2615599)
        assert isinstance(parsed, dict)
        assert isinstance(diagnosis, str)
        assert "组织学类型" in parsed
        assert "腺癌" in parsed.get("组织学类型", "")
        assert "病理分期" in parsed

    def test_parse_pathology_2615597(self, pathology_text_2615597):
        """病理诊断解析 - 2615597（息肉/腺瘤）"""
        parsed, diagnosis = parse_pathology(pathology_text_2615597)
        assert isinstance(parsed, dict)
        assert isinstance(diagnosis, str)
        # 2615597 诊断含"增生性息肉"或"绒毛状腺瘤"
        assert any(kw in diagnosis for kw in ["息肉", "腺瘤"])

    def test_all_parsers_handle_empty_text(self):
        """所有解析器对空文本应优雅降级"""
        for parser in [parse_dna, parse_tct, parse_hpv,
                       parse_cytology, parse_pathology, parse_gastric]:
            parsed, diagnosis = parser("")
            assert isinstance(parsed, dict), f"{parser.__name__} should return dict"
            assert isinstance(diagnosis, str), f"{parser.__name__} should return str"
