"""FHIR R4 Bundle 生成器"""

from datetime import date
import uuid


def generate_fhir_bundle(
    pathology_id: str = "",
    patient_name: str = "",
    gender: str = "",
    age: int = None,
    report_type: str = "",
    report_date=None,
    diagnosis: str = "",
    parsed_data: dict = None
) -> dict:
    """将解析后的数据转换为FHIR R4 Bundle"""

    bundle_id = str(uuid.uuid4())
    diag_id = pathology_id or f"DR-{bundle_id[:8]}"

    entry = []

    # DiagnosticReport 资源
    diagnostic_report = {
        "resourceType": "DiagnosticReport",
        "id": diag_id,
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": _loinc_code(report_type),
                    "display": _loinc_display(report_type)
                }
            ],
            "text": _report_type_label(report_type)
        },
        "subject": {
            "display": patient_name
        },
        "effectiveDateTime": str(report_date) if report_date else None,
        "issued": str(date.today().isoformat()),
        "performer": [
            {
                "display": "上海衡道医学病理诊断中心"
            }
        ],
        "conclusion": diagnosis
    }

    # 如果有年龄/性别，补充subject引用
    if age:
        diagnostic_report["extension"] = [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-age",
                "valueAge": {
                    "value": age,
                    "unit": "岁",
                    "system": "http://unitsofmeasure.org",
                    "code": "a"
                }
            }
        ]

    entry.append({"resource": diagnostic_report})

    # Observation 资源（如有结构化数据）
    if parsed_data:
        obs_index = 1
        for key, value in parsed_data.items():
            if isinstance(value, (str, int, float)):
                obs = {
                    "resourceType": "Observation",
                    "id": f"{diag_id}-obs-{obs_index}",
                    "status": "final",
                    "code": {
                        "text": key
                    },
                    "valueString": str(value) if not isinstance(value, (int, float)) else None,
                    "valueQuantity": _to_quantity(value) if isinstance(value, (int, float)) else None,
                    "derivedFrom": [
                        {"reference": f"DiagnosticReport/{diag_id}"}
                    ]
                }
                # 清理None值
                obs = {k: v for k, v in obs.items() if v is not None}
                entry.append({"resource": obs})
                obs_index += 1

    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": "collection",
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "entry": entry
    }


def _loinc_code(report_type: str) -> str:
    codes = {
        "细胞学（妇科）": "47527-7",
        "HPV检测": "21440-3",
        "细胞学（非妇科）": "47527-7",
        "常规病理": "60568-3",
    }
    return codes.get(report_type, "60568-3")


def _loinc_display(report_type: str) -> str:
    names = {
        "细胞学（妇科）": "Cytology report (gynecologic)",
        "HPV检测": "HPV DNA test",
        "细胞学（非妇科）": "Cytology report (non-gynecologic)",
        "常规病理": "Surgical pathology report",
    }
    return names.get(report_type, "Pathology report")


def _report_type_label(report_type: str) -> str:
    return report_type


def _to_quantity(value) -> dict | None:
    if isinstance(value, (int, float)):
        return {"value": value}
    return None
