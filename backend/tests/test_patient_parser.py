"""患者信息解析器测试"""
from src.parsers.patient_parser import parse_patient_info


class TestPatientParser:
    """通用患者信息提取"""

    def test_extract_dna_patient(self, dna_text):
        """DNA 报告：提取性别/年龄/病理号/医院（注：DNA 报告姓名格式为 \"姓名 侯杰十\" 无冒号，无法匹配）"""
        info = parse_patient_info(dna_text)
        assert info["pathology_id"] == "F2608174"
        assert info["gender"] == "女"
        assert info["age"] == 29
        assert "某市人民医院" in info.get("hospital", "")
        assert info["specimen_type"] == "宫颈刷取物"

    def test_extract_tct_patient(self, tct_text):
        """TCT 报告：提取患者信息（与 DNA 同一病理号）"""
        info = parse_patient_info(tct_text)
        assert info["patient_name"] == "侯杰十"
        assert info["gender"] == "女"
        assert info["pathology_id"] == "F2608174"

    def test_extract_hpv_patient(self, hpv_text):
        """HPV 报告：提取患者信息"""
        info = parse_patient_info(hpv_text)
        assert info["patient_name"] == "侯杰十"
        assert info["gender"] == "女"
        assert info["age"] == 29
        assert info["pathology_id"] == "V2605675"

    def test_extract_cytology_patient(self, cytology_text):
        """细胞学（非妇科）报告：提取患者信息"""
        info = parse_patient_info(cytology_text)
        assert info["patient_name"] == "姚秀刚"
        assert info["gender"] == "女"
        assert info["age"] == 68
        assert info["pathology_id"] == "N2604120"
        assert "腹水" in info.get("specimen_type", "")

    def test_extract_pathology_patient(self, pathology_text_2615599):
        """常规病理报告：提取患者信息"""
        info = parse_patient_info(pathology_text_2615599)
        assert info["patient_name"] == "苏勇勇"
        assert info["gender"] == "女"
        assert info["age"] == 36
        assert info["pathology_id"] == "2615599"
        assert "外二科" in info.get("department", "")

    def test_empty_text(self):
        """空文本返回空字典"""
        info = parse_patient_info("")
        assert info == {}

    def test_incomplete_text(self):
        """不完整文本：优雅降级"""
        info = parse_patient_info("姓名：张三  性别：男")
        assert info["patient_name"] == "张三"
        assert info["gender"] == "男"
        assert "pathology_id" not in info
        assert "age" not in info
