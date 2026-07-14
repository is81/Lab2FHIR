"""FHIR Bundle 生成器测试"""
import datetime
from src.fhir.generator import generate_fhir_bundle


class TestFhirGenerator:
    """FHIR R4 Bundle 生成"""

    def test_generates_valid_bundle_structure(self):
        bundle = generate_fhir_bundle(
            pathology_id="F2608174",
            patient_name="侯杰十",
            gender="女",
            age=29,
            report_type="细胞学（妇科）",
            report_date=datetime.date(2026, 5, 2),
            diagnosis="未见DNA倍体异常细胞",
            parsed_data={"细胞总数": 6687, "DNA检测结果": "未见DNA倍体异常细胞"}
        )
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "collection"
        assert "id" in bundle
        assert "timestamp" in bundle
        assert "entry" in bundle
        assert len(bundle["entry"]) >= 1  # 至少 DiagnosticReport

    def test_diagnostic_report_in_bundle(self):
        bundle = generate_fhir_bundle(
            pathology_id="V2605675",
            patient_name="侯杰十",
            gender="女",
            age=29,
            report_type="HPV检测",
            diagnosis="低危型HPV：阳性-HPV54",
            parsed_data={"高危型HPV": "阴性", "低危型HPV": "阳性-HPV54"}
        )
        dr = [e["resource"] for e in bundle["entry"]
              if e["resource"]["resourceType"] == "DiagnosticReport"]
        assert len(dr) == 1
        assert dr[0]["status"] == "final"
        assert dr[0]["subject"]["display"] == "侯杰十"

    def test_observations_for_scalar_values(self):
        bundle = generate_fhir_bundle(
            pathology_id="TEST",
            patient_name="测试",
            report_type="常规病理",
            parsed_data={"长度": 1.0, "诊断": "阴性"}
        )
        obs = [e["resource"] for e in bundle["entry"]
               if e["resource"]["resourceType"] == "Observation"]
        assert len(obs) >= 2  # 两个 scalar 值各生成一个 Observation

    def test_empty_parsed_data_no_observations(self):
        bundle = generate_fhir_bundle(
            pathology_id="T001",
            patient_name="测试",
            report_type="常规病理",
            diagnosis="无异常",
            parsed_data={}
        )
        obs = [e["resource"] for e in bundle["entry"]
               if e["resource"]["resourceType"] == "Observation"]
        assert len(obs) == 0

    def test_loinc_codes_by_type(self):
        """每种报告类型有对应的 LOINC 编码"""
        dna_bundle = generate_fhir_bundle(
            pathology_id="T1", patient_name="P1", report_type="细胞学（妇科）", parsed_data={}
        )
        hpv_bundle = generate_fhir_bundle(
            pathology_id="T2", patient_name="P2", report_type="HPV检测", parsed_data={}
        )
        path_bundle = generate_fhir_bundle(
            pathology_id="T3", patient_name="P3", report_type="常规病理", parsed_data={}
        )

        def get_code(bundle):
            dr = bundle["entry"][0]["resource"]
            return dr["code"]["coding"][0]["code"]

        assert get_code(dna_bundle) == "47527-7"
        assert get_code(hpv_bundle) == "21440-3"
        assert get_code(path_bundle) == "60568-3"

    def test_bundle_id_is_unique(self):
        b1 = generate_fhir_bundle(pathology_id="A1", patient_name="P", report_type="常规病理", parsed_data={})
        b2 = generate_fhir_bundle(pathology_id="A2", patient_name="P", report_type="常规病理", parsed_data={})
        assert b1["id"] != b2["id"]

    def test_extension_for_age(self):
        bundle = generate_fhir_bundle(
            pathology_id="T1", patient_name="P1", age=45,
            report_type="常规病理", parsed_data={}
        )
        dr = bundle["entry"][0]["resource"]
        ext = dr.get("extension", [])
        assert len(ext) >= 1
        assert ext[0]["valueAge"]["value"] == 45
        assert ext[0]["valueAge"]["unit"] == "岁"

    def test_no_extension_without_age(self):
        bundle = generate_fhir_bundle(
            pathology_id="T1", patient_name="P1",
            report_type="常规病理", parsed_data={}
        )
        dr = bundle["entry"][0]["resource"]
        assert "extension" not in dr
