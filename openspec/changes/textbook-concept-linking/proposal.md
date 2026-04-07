## Why

当前数学知识图谱已有 1,275 个 Concept 和 2,810 个 Statement，但缺少教材章节与知识点的关联。老师无法按教材查询知识点，学生无法知道自己学习了哪些章节的知识点。

同时，教育局课标 PDF 是扫描版，需要 OCR 识别才能提取知识点作为权威基准。

## What Changes

- 新增教材章节节点 `textbook_chapter`，通过属性区分不同教材版本和学科
- 新增 `CONTAINS` 关系，关联章节到 Concept
- 新增教材导入服务，解析 JSON 格式教材数据并导入 Neo4j
- 新增知识点关联服务，支持精确匹配、模糊匹配、人工确认
- 新增 PDF OCR 服务，用于课标识别和后续作业切题

## Capabilities

### New Capabilities

- `textbook-import`: 教材导入服务，解析教材 JSON 数据，创建章节节点，关联知识点
- `concept-linking`: 知识点关联服务，支持教材知识点与 Concept 匹配，输出匹配报告
- `pdf-ocr`: PDF OCR 服务，支持扫描版 PDF 识别，课标知识点提取，后续支持作业切题

### Modified Capabilities

- 无

## Impact

### 新增模块

```
ai-edu-ai-service/
├── core/
│   ├── ocr/                    # OCR 模块
│   │   ├── pdf_ocr.py          # PDF 识别
│   │   └── homework_cutter.py  # 作业切题（后续）
│   │
│   └── kg/
│       └── textbook/           # 教材模块
│           ├── parser.py       # 教材解析
│           ├── linker.py       # 知识点关联
│           └── importer.py     # 导入服务
│
└── api/
    └── kg/
        └── textbook.py         # 教材 API
```

### 数据变更

```
Neo4j 新增:
├── textbook_chapter 节点（统一类型，属性区分）
│   ├── name: "人教版_数学_七年级_上册_第一章_有理数"
│   ├── publisher: "人教版"      # 人教版/北师大版/苏教版...
│   ├── subject: "数学"          # 数学/物理/化学/语文...
│   ├── grade: "七年级"          # 一年级~十二年级
│   ├── semester: "上册"         # 上册/下册
│   ├── chapter: "第一章有理数"
│   └── order: 1
│
└── CONTAINS 关系
    └── Chapter -[:CONTAINS]-> Concept
```

### 依赖

- OCR: PaddleOCR 或 PyMuPDF
- Neo4j: 已有连接
- LLM: 用于知识点语义匹配