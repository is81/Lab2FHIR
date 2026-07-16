# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目概述

Lab2FHIR 将非结构化的化验/病理 PDF 报告转换为 **HL7 FHIR R4** 格式。这是一个全栈应用，后端使用 **FastAPI**，前端使用 **Vue 3 + Element Plus**。目标用户是进行历史病历数字化的医院 IT 团队。

全部 404 份 PDF 样本位于 `docs/pdf_test/`。它们都是文本型 PDF（非扫描件），无需 OCR —— pdfplumber 直接提取文本。

## 启动命令

```bash
# 后端（端口 8000）
cd f:/Lab2FHIR
pip install -r backend/requirements.txt
python -m uvicorn backend.src.api.main:app --host 0.0.0.0 --port 8000 --reload

# 前端（端口 5173，/api 代理至 localhost:8000）
cd f:/Lab2FHIR/frontend
npm install
npm run dev

# 前端生产构建
npm run build
```

API 文档自动生成于 `http://localhost:8000/docs`（Swagger）。

## 架构

```
PDF 文件 (docs/pdf_test/)
  → extractors/base.py      extract_text() 通过 pdfplumber 提取文本
  → identify_report_type()  标题关键词 + 文件名模式识别报告类型
  → parsers/patient_parser  解析姓名/性别/年龄/医院/日期
  → parsers/{dna,tct,hpv}_parser  提取结构化数据 + 诊断结论
  → fhir/generator.py       构建 FHIR R4 Bundle（DiagnosticReport + Observation）
  → db/models.py            存入 SQLite（Report 表：raw_text, parsed_data JSON, fhir_bundle JSON）
  → api/routes_*.py         通过 REST API 和前端提供服务
```

### 核心模块

| 模块 | 用途 |
|------|------|
| `backend/src/extractors/base.py` | PDF 文本提取 + 报告类型识别 |
| `backend/src/parsers/` | DNA/TCT/HPV 等解析器 + 通用患者信息解析 |
| `backend/src/fhir/generator.py` | FHIR R4 Bundle，含每种报告类型的 LOINC 编码 |
| `backend/src/db/` | SQLAlchemy ORM（`Report` 模型）+ Repository 模式 |
| `backend/src/api/` | FastAPI 路由：`/api/convert`、`/api/reports`、`/api/stats`、`/api/pdf/` |
| `frontend/src/views/` | 5 个页面：Dashboard、ImportView、ReportList、ReportDetail、PatientView |
| `frontend/src/api/index.js` | Axios 封装，调用后端 `/api/*` 接口 |

### 已识别的报告类型（6 种）

| 类型 | 病理号前缀 | 识别方式 | 数量 |
|------|:---:|---|---:|
| DNA | F-series | 文本："DNA定量细胞学检查报告" | 65 |
| TCT | F-series | 文本："液基薄层细胞学检测报告" | 77 |
| HPV | V-series | 文本："人乳头状瘤病毒" | 79 |
| 细胞学 | N-series | 文本："细胞学报告单" | 13 |
| 胃镜 | 26-series | 评分表头（"慢性炎症"+"活动性"+"萎缩"） | 87 |
| 病理诊断 | 26-series, B-series | 标题含"病理诊断"+"报告单"（排除以上类型后兜底） | 83 |

### 数据库

SQLite 数据库位于 `backend/lab2fhir.db`。`Report` 模型同时存储原始提取文本（`raw_text`）、结构化数据（`parsed_data` JSON）和最终的 `fhir_bundle` JSON。唯一键为 `(pathology_id, report_type)` —— 同一病理号可对应多种报告类型（如 F2608174 同时是该患者的 DNA 和 TCT 报告）。

### 前端路由

- `/` — 首页仪表盘（统计卡片 + 类型分布柱状图）
- `/import` — 拖拽上传 PDF，通过 `/api/convert` 批量导入
- `/reports` — 可搜索表格（姓名/类型/日期），通过 `/api/reports` 分页
- `/reports/:id` — 三栏布局：解析结果 | PDF 原文 | FHIR JSON
- `/patients/:name` — 患者报告时间线

## 浏览器兼容性

| 浏览器 | 最低版本 | 制约因素 |
|--------|----------|----------|
| Chrome | 92 | pdfjs-dist 4.x（`.at()` + 私有字段，`legacy/` 构建未消除） |
| Firefox | 90 | 同上 |
| Safari | 15.4 | 同上 |
| Edge | 92 | 同 Chrome |

- JS/CSS/Vue3/Element Plus 代码本身兼容 Chrome 85+，唯一硬约束是 pdfjs-dist 4.x。
- 若需下探至 Chrome 85：降级 pdfjs-dist 至 `^3.11.174` + `vite.config.js` 加 `build.target: 'chrome85'`。
- `browserslist` 定义在 `frontend/package.json`。

## 重要注意事项

**终端中文乱码**：Windows Git Bash 默认使用 GBK 编码，Python 打印中文时出现乱码。解决方案：在 Python 命令前加 `PYTHONIOENCODING=utf-8`，或在 shell 中设置 `export PYTHONIOENCODING=utf-8`。读取中文输出时，建议先写入 UTF-8 文件再使用 Read 工具查看。

**Windows 中文文件名编码问题**：`os.listdir()` 因 GBK/UTF-8 不匹配返回乱码文件名。`/api/reports/{id}/pdf?pid=` 接口使用**病理号模糊匹配**在 `docs/pdf_test/` 中查找文件，而非文件名匹配。始终使用病理号查找，不要依赖精确文件名匹配。

**报告类型识别顺序很重要**：胃镜报告与普通病理诊断报告共享标题"病理诊断报告单"。文本识别必须先检查胃镜评分表特征（`慢性炎症` + `活动性` + `萎缩`），**再**回退到"病理诊断"匹配。参见 `extractors/base.py` 中的 `identify_report_type()`。

**同一病理号、不同报告类型**：`F` 前缀病理号在同一患者的 DNA 和 TCT 报告之间共享。去重必须使用 `(pathology_id, report_type)` 作为复合键，不能仅用 pathology_id。

**全部 PDF 为文本型**：pdfplumber 可处理全部 405 份样本。当前数据集中不存在扫描件/图片型 PDF，因此暂时不需要 PaddleOCR/Tesseract 集成。
