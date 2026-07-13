# Lab2FHIR

> 化验单 PDF → HL7 FHIR R4 · 开源医疗数据数字化工具  
> Lab Report PDF → HL7 FHIR R4 · Open-source Medical Data Digitization Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-green.svg)](https://www.python.org/)
[![Vue 3](https://img.shields.io/badge/Vue-3.x-brightgreen.svg)](https://vuejs.org/)

Lab2FHIR 将非结构化的化验/病理 PDF 报告自动转换为国际标准的 **HL7 FHIR R4** 格式。如同一个"化验单翻译官"，打通非结构化数据与现代化医疗信息系统之间的壁垒。

Lab2FHIR automatically converts unstructured lab/pathology PDF reports into the international standard **HL7 FHIR R4** format — bridging the gap between unstructured data and modern healthcare information systems.

---

## 功能特性 / Features

- **PDF 自动解析** — 提取患者信息、检测结果、诊断结论，支持 4 大类报告
- **FHIR R4 输出** — 生成标准 DiagnosticReport + Observation Bundle，含 LOINC 编码
- **Web 操作界面** — 拖拽批量导入、全文搜索、PDF 原文对照查看
- **轻量部署** — SQLite + FastAPI，无需外部数据库

## 支持的报告类型 / Supported Report Types

| 类型 / Type | 说明 / Description | 示例数量 |
|------|------|:--:|
| 细胞学（妇科） | DNA 倍体 + TCT 液基细胞学 | 142 |
| HPV检测 | 人乳头状瘤病毒基因分型 | 79 |
| 细胞学（非妇科） | 穿刺/脱落细胞学检查 | 13 |
| 常规病理 | 胃镜病理 + 外科病理诊断 | 170 |

## 快速开始 / Quick Start

### 环境要求 / Prerequisites

- Python 3.9+
- Node.js 18+

### 安装运行 / Installation

```bash
# 克隆仓库 / Clone
git clone https://github.com/is81/Lab2FHIR.git
cd Lab2FHIR

# 后端 / Backend
pip install -r backend/requirements.txt
python -m uvicorn backend.src.api.main:app --host 0.0.0.0 --port 8000

# 前端（新终端） / Frontend (new terminal)
cd frontend
npm install
npm run dev
```

打开浏览器访问 / Open browser: **http://localhost:5173**

### 导入数据 / Import Data

将 PDF 报告放入 `docs/pdf_test/`，然后通过 Web 界面拖拽导入，或调用 API：

```bash
curl -X POST http://localhost:8000/api/convert \
  -F "file=@your_report.pdf"
```

## API 端点

| 端点 | 方法 | 说明 |
|------|:--:|------|
| `/api/convert` | POST | 上传 PDF → 解析 → FHIR Bundle |
| `/api/reports` | GET | 搜索、筛选、分页查询报告 |
| `/api/reports/{id}` | GET | 报告详情（含结构化数据 + FHIR JSON） |
| `/api/reports/{id}/pdf` | GET | 原始 PDF 文件 |
| `/api/stats` | GET | 统计概览 |
| `/api/health` | GET | 健康检查 |

完整 API 文档自动生成：http://localhost:8000/docs

## 技术栈 / Tech Stack

| 层 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| PDF 提取 | pdfplumber |
| 数据库 | SQLite + SQLAlchemy + FTS5 |
| 前端框架 | Vue 3 + Element Plus |
| PDF 渲染 | PDF.js |
| 标准 | HL7 FHIR R4 + LOINC |

## 项目结构 / Project Structure

```
Lab2FHIR/
├── backend/
│   ├── requirements.txt
│   └── src/
│       ├── api/              # FastAPI 路由
│       ├── db/               # 数据库模型 + FTS5 全文索引
│       ├── extractors/       # PDF 文本提取 + 报告类型识别
│       ├── parsers/          # 各类型报告解析器
│       └── fhir/             # FHIR R4 Bundle 生成器
├── frontend/
│   └── src/
│       ├── views/            # 5 个页面组件
│       ├── components/       # 可复用组件（PdfViewer）
│       └── utils/            # 共享工具函数
├── docs/
│   ├── pdf_test/             # PDF 测试样本
│   ├── 项目计划.md
│   └── 代码审查报告.md
├── LICENSE                   # MIT
└── README.md
```

## 贡献 / Contributing

欢迎提交 Issue 和 Pull Request。请确保：

1. 新功能有对应的测试覆盖
2. 代码风格保持一致
3. 通过 `npm run build` 构建验证

## 许可证 / License

[MIT](LICENSE)
