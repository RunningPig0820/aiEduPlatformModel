## Why

教育局课标 PDF 是权威的知识点基准，但目前是扫描版无法直接提取。EduKG 数据已导入 Neo4j，但缺少小学知识点。需要分析教育局课标，提取知识点结构，生成标准格式文件供后续导入模块使用。

## What Changes

- 新增课标 PDF OCR 识别服务，提取文本内容
- 新增知识点提取服务，使用 LLM 从 OCR 文本中提取结构化知识点
- 新增知识点对比分析服务，与已导入的 EduKG Concept 对比
- 生成 JSON/TTL 格式输出文件，不直接导入 Neo4j
- 使用免费大模型（glm-4-flash）处理知识点匹配

## Capabilities

### New Capabilities

- `pdf-ocr`: PDF OCR 识别服务，提取扫描版 PDF 文本内容
- `kp-extraction`: 知识点提取服务，使用 LLM 从文本提取结构化知识点
- `kp-comparison`: 知识点对比服务，分析教育局知识点与 EduKG Concept 的差异

### Modified Capabilities

- 无

## Impact

### 输出文件

```
edukg/data/eduBureau/math/
├── ocr_result.json              # OCR 识别结果
├── curriculum_kps.json          # 提取的知识点结构
├── kp_comparison_report.json    # 与 EduKG 对比报告
└── curriculum_kps.ttl           # TTL 格式输出（可选）
```

### 依赖

- OCR: 百度 OCR API（已有账号）
- LLM: 智谱 glm-4-flash（免费）
- 已导入数据: EduKG Concept（Neo4j）

### 数据流程

```
课标 PDF → OCR识别 → 文本提取 → LLM结构化 → 知识点列表 → 对比分析 → JSON/TTL输出
```