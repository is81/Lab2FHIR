#!/usr/bin/env python
"""Excel 交叉验证工具 —— 将 202605.xls 中的诊断字段与 PDF 解析结果比对

用法:
    PYTHONIOENCODING=utf-8 python tools/validate_with_excel.py --excel docs/202605.xls

前提: 数据库已导入所有 PDF（404 份），Excel 存在于 docs/ 目录。
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import argparse
import pandas as pd
from db.models import SessionLocal, Report
from parsers.patient_parser import parse_patient_info


def load_excel(path: str) -> pd.DataFrame:
    """加载 Excel 索引文件"""
    df = pd.read_excel(path, engine="xlrd" if path.endswith(".xls") else "openpyxl")
    print(f"[Excel] 加载 {len(df)} 条记录\n  列名: {list(df.columns)}")
    return df


def validate(db, df: pd.DataFrame) -> dict:
    """交叉验证：比对 DB 中的解析结果与 Excel 中的诊断"""
    # 构建 pid → excel_row 索引
    pid_col = None
    diag_col = None
    name_col = None
    for col in df.columns:
        if "病理号" in str(col):
            pid_col = col
        elif "病理所见" in str(col) or "诊断" in str(col):
            diag_col = col
        elif "姓名" in str(col):
            name_col = col

    if not pid_col or not diag_col:
        print(f"[WARN] 找不到 病理号/病理所见 列，可用列: {list(df.columns)}")
        return {"total": 0, "matched": 0, "unmatched": [], "missing_in_db": []}

    excel_map: dict[str, dict] = {}
    for _, row in df.iterrows():
        pid = str(row[pid_col]).strip()
        if pid and pid != "nan":
            excel_map[pid] = {
                "diagnosis": str(row[diag_col]).strip() if pd.notna(row[diag_col]) else "",
                "name": str(row[name_col]).strip() if name_col and pd.notna(row[name_col]) else "",
            }

    stats = {"total": len(excel_map), "matched": 0, "unmatched": [], "missing_in_db": []}

    # 遍历 DB 报告
    reports = db.query(Report).all()
    db_pids = set()

    for r in reports:
        db_pids.add(r.pathology_id)
        if r.pathology_id in excel_map:
            excel_diag = excel_map[r.pathology_id]["diagnosis"]
            excel_name = excel_map[r.pathology_id]["name"]

            issues = []

            # 姓名验证
            if excel_name and r.patient_name and excel_name not in r.patient_name and r.patient_name not in excel_name:
                issues.append(f"姓名不匹配: DB={r.patient_name}, Excel={excel_name}")

            # 诊断验证（模糊匹配：Excel 关键词是否出现在 DB 诊断中）
            if excel_diag and r.diagnosis:
                # 取前20个有意义的字符比较
                excel_kw = excel_diag[:30].strip()
                if excel_kw and excel_kw not in r.diagnosis:
                    # 尝试更宽松的匹配：取关键词
                    found = any(word in r.diagnosis for word in excel_kw.replace("，", ",").replace("。", "").split(",") if len(word) >= 4)
                    if not found:
                        issues.append(f"诊断不匹配: DB摘要={r.diagnosis_summary}, Excel摘要={excel_kw}")

            if issues:
                stats["unmatched"].append({
                    "pathology_id": r.pathology_id,
                    "report_type": r.report_type,
                    "issues": issues,
                })
            else:
                stats["matched"] += 1

    # Excel 中有但 DB 中没有的
    for pid in excel_map:
        if pid not in db_pids:
            stats["missing_in_db"].append(pid)

    return stats


def print_report(stats: dict):
    """打印验证报告"""
    print("\n" + "=" * 60)
    print("  交叉验证报告")
    print("=" * 60)
    print(f"  Excel 总记录:   {stats['total']}")
    print(f"  匹配通过:       {stats['matched']} ({100*stats['matched']/max(stats['total'],1):.1f}%)")
    print(f"  不匹配:         {len(stats['unmatched'])}")
    print(f"  Excel有/DB无:   {len(stats['missing_in_db'])}")

    if stats["unmatched"]:
        print(f"\n--- 不匹配明细 ({len(stats['unmatched'])} 条) ---")
        for item in stats["unmatched"][:20]:  # 最多显示 20 条
            print(f"  [{item['pathology_id']}] ({item['report_type']})")
            for issue in item["issues"]:
                print(f"    - {issue}")

    if stats["missing_in_db"]:
        print(f"\n--- Excel有/DB无 ({len(stats['missing_in_db'])} 条) ---")
        for pid in stats["missing_in_db"][:10]:
            print(f"  - {pid}")
        if len(stats["missing_in_db"]) > 10:
            print(f"  ... 还有 {len(stats['missing_in_db']) - 10} 条")


def main():
    parser = argparse.ArgumentParser(description="Excel 交叉验证")
    parser.add_argument("--excel", required=True, help="Excel 索引文件路径")
    args = parser.parse_args()

    df = load_excel(args.excel)
    db = SessionLocal()
    try:
        stats = validate(db, df)
        print_report(stats)
    finally:
        db.close()


if __name__ == "__main__":
    main()
