## Why

当前数学知识图谱已有 1,275 个 Concept 和 2,810 个 Statement，但缺少教材章节与知识点的关联。老师无法按教材查询知识点，学生无法知道自己学习了哪些章节的知识点。

同时，教育局课标 PDF 是扫描版，需要 OCR 识别才能提取知识点作为权威基准。EduKG 数据已导入 Neo4j，但缺少小学知识点。

## What Changes

- 解析教材 JSON 数据，生成 `textbook_chapters.json` 章节结构文件
- 匹配教材知识点与 EduKG Concept，生成 `matching_report.json` 匹配报告
- 使用百度 OCR API 识别课标 PDF（收费服务），提取文本内容
- 使用免费 LLM (glm-4-flash) 从课标文本提取结构化知识点
- 与 Neo4j 已有 Concept 对比分析，生成 `kp_comparison_report.json`
- 输出 JSON/TTL 格式文件，不直接导入 Neo4j（人工确认后手动导入）

## Capabilities

### New Capabilities

- `textbook-parse`: 教材解析服务，解析教材 JSON 数据，生成章节结构文件
- `concept-match`: 知识点匹配服务，查询 Neo4j Concept，生成匹配报告
- `pdf-ocr`: PDF OCR 服务，使用百度 OCR API（收费）识别扫描版 PDF
- `kp-extract`: 知识点提取服务，使用 LLM 从课标文本提取结构化知识点
- `kp-compare`: 知识点对比服务，分析课标知识点与 EduKG Concept 的差异

### Modified Capabilities

- 无

## Impact

### 输出文件

```
edukg/data/output/
├── textbook_chapters.json         # 教材章节结构
├── matching_report.json           # 教材知识点匹配报告
├── ocr_result.json                # OCR 识别结果
├── curriculum_kps.json            # 课标知识点结构
├── kp_comparison_report.json      # 与 EduKG 对比报告
└── curriculum_kps.ttl             # TTL 格式输出
```

### 新增模块

```
edukg/core/
├── textbook/                      # 教材模块
│   ├── parser.py                  # 教材解析
│   ├── matcher.py                 # 知识点匹配
│   └── main.py                    # 主脚本（整合流程）
│
└── curriculum/                    # 课标模块
    ├── pdf_ocr.py                 # PDF OCR（百度 API，收费）
    ├── kp_extraction.py           # 知识点提取（LLM）
    ├── kp_comparison.py           # 知识点对比
    ├── ttl_generator.py           # TTL 生成
    └── main.py                    # 主脚本（整合流程）
```

### 依赖

- OCR: 百度 OCR API（收费，用户已有账号）
- LLM: 智谱 glm-4-flash（免费）
- Neo4j: 查询 EduKG Concept（只读，不导入）

### 数据流程

```
教材 JSON → 解析 → textbook_chapters.json
         → 匹配 Neo4j Concept → matching_report.json

课标 PDF → 百度 OCR（收费）→ ocr_result.json
        → LLM 提取（免费）→ curriculum_kps.json
        → 对比 Neo4j → kp_comparison_report.json
        → TTL 生成 → curriculum_kps.ttl
```

### 导入方式

**人工确认后手动导入**：
- 脚本只生成 JSON/TTL 文件
- 用户人工确认匹配报告
- 用户手动执行 Neo4j 导入脚本