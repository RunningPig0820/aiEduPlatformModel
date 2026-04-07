## Context

### 当前状态

```
Neo4j 数学知识图谱:
├── Class: 38 个（概念类）
├── Concept: 1,275 个（知识点）
├── Statement: 2,810 个（定义/定理）
└── 关系: SUB_CLASS_OF, HAS_TYPE, RELATED_TO, PART_OF, BELONGS_TO

教育局课标:
├── 义务教育数学课程标准（2022年版）.pdf (40MB, 189页)
├── 扫描版，需要 OCR 识别
└── 包含学段、领域、知识点结构
```

### 约束

- 课标 PDF 是扫描版，无法直接提取文本
- EduKG 主要覆盖初中和高中，缺少小学知识点
- 不做导入操作，只生成 JSON/TTL 文件
- 使用免费大模型（glm-4-flash）

## Goals / Non-Goals

**Goals:**

1. OCR 识别课标 PDF，提取文本内容
2. 使用 LLM 从文本中提取结构化知识点（学段、领域、知识点）
3. 与已导入的 EduKG Concept 对比，分析差异
4. 生成 JSON/TTL 格式输出文件

**Non-Goals:**

1. 不导入 Neo4j（由专门导入模块处理）
2. 不实现教材章节关联（由 textbook-concept-linking 模块处理）
3. 不实现作业切题功能
4. 不处理其他学科（物理、化学）

## Decisions

### 1. OCR 技术选型

**决策**: 使用百度 OCR API

**理由**:
- 已有百度 OCR API 账号，无需额外部署
- 中文识别效果好，准确率高
- API 调用简单，无需本地 GPU
- 支持表格、公式识别
- 按调用次数计费，成本可控

**替代方案**:
- ❌ PaddleOCR 本地部署: 需要安装配置，占用资源
- ❌ Tesseract: 中文效果差

### 2. LLM 技术选型

**决策**: 使用智谱 glm-4-flash（免费）

**理由**:
- 完全免费
- 中文效果好
- 支持结构化输出
- API 稳定

**替代方案**:
- ❌ DeepSeek: 需付费
- ❌ 百炼 qwen: 需付费

### 3. 输出格式

**决策**: 生成 JSON + TTL 双格式

**理由**:
- JSON: 易于阅读、调试、人工确认
- TTL: 符合知识图谱标准，可直接导入 Neo4j

**替代方案**:
- ❌ 仅 JSON: 后续导入需要额外转换
- ❌ 仅 TTL: 不便于人工查看确认

### 4. 处理流程

**决策**: 分步处理，中间结果可保存

```
Step 1: OCR → ocr_result.json
        ├── 每页文本内容
        └── 保存原始结果，便于调试

Step 2: LLM 提取 → curriculum_kps.json
        ├── 按学段组织
        ├── 按领域分类
        └── 知识点列表

Step 3: 对比分析 → kp_comparison_report.json
        ├── 与 EduKG Concept 对比
        ├── 已存在知识点
        └── 新增知识点（小学为主）

Step 4: TTL 输出 → curriculum_kps.ttl
        └── 标准格式，供导入模块使用
```

**理由**:
- 每步独立，可单独调试
- 中间结果可保存，避免重复处理
- OCR 耗时，结果需缓存

## Risks / Trade-offs

### Risk 1: OCR 识别准确率

**风险**: 课标 PDF 扫描质量影响 OCR 准确率

**缓解**:
- 人工校验 OCR 结果
- 提取后人工整理知识点列表
- 不直接导入，先确认再入库

### Risk 2: LLM 提取格式不稳定

**风险**: LLM 输出格式可能不一致

**缓解**:
- 使用结构化输出 prompt
- 多次尝试，人工校验
- 提供 JSON schema 作为示例

### Risk 3: 小学知识点大量新增

**风险**: EduKG 缺少小学知识点，对比报告可能显示大量新增

**缓解**:
- 这是预期结果，符合目标
- 新增知识点由导入模块处理
- 先生成报告，再决定导入策略

## Migration Plan

不需要迁移，仅生成数据文件。

### 验证步骤

```bash
1. 运行 OCR，检查 ocr_result.json 文本质量
2. 运行 LLM 提取，检查 curriculum_kps.json 结构
3. 运行对比分析，检查 kp_comparison_report.json
4. 人工确认知识点列表
```