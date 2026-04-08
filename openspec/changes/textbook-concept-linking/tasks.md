## 开发流程说明

**重要：分阶段开发，每个阶段完成后需验证再继续下一阶段**

```
阶段1 → 运行测试 → 人工确认 → 阶段2 → 运行测试 → 人工确认 → ...
```

每个阶段完成后：
1. 运行该阶段的测试用例 `pytest tests/curriculum/test_xxx.py -v`
2. 确认测试通过后，通知人工启动下一阶段
3. 如有失败，修复问题后重新测试

---

## Part 1: 课标知识点提取（代码已完成）

> **状态**: 代码已完成，但未生成实际数据
> **原因**: LLM 调用超时，需要分步执行控制

### 1. 项目结构初始化（阶段1）✅ 已完成

- [x] 1.1 创建 `edukg/core/curriculum/` 目录结构
- [x] 1.2 创建测试目录 `tests/curriculum/`
- [x] 1.3 配置百度 OCR API Key 环境变量 (BAIDU_OCR_API_KEY, BAIDU_OCR_SECRET_KEY)
- [x] 1.4 配置智谱 API Key 环境变量（ZHIPU_API_KEY）
- [x] 1.5 配置 Neo4j 环境变量（NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD）

---

### 2. PDF OCR 服务（阶段2）✅ 已完成

**目标**: 使用百度 OCR API 识别课标 PDF（收费服务）

- [x] 2.1 实现 `BaiduOCRService` 类，初始化百度 OCR API 客户端
- [x] 2.2 实现 `extract_text()` 调用百度 OCR API 提取文字
- [x] 2.3 实现 PDF 转图片 + OCR 识别流程
- [x] 2.4 实现 `save_ocr_result()` 保存 OCR 结果到 JSON
- [x] 2.5 处理 API 调用限制（QPS、错误重试、成本控制）
- [x] 2.6 完成 189页 PDF 的 OCR 识别

**输出**: `edukg/data/eduBureau/math/ocr_result.json` ✅ 已生成

---

### 3. 知识点提取服务（阶段3）✅ 代码完成

**目标**: 使用 LLM 从课标文本提取结构化知识点

> **LLM使用**: glm-4-flash（免费），从OCR文本中识别结构化知识点

- [x] 3.1 实现 `LLMExtractor` 类，配置 ChatZhipuAI (glm-4-flash，免费)
- [x] 3.2 设计结构化 prompt，要求 JSON 输出
- [x] 3.3 实现 `extract_knowledge_points()` 提取学段、领域、知识点
- [x] 3.4 实现文本分块处理（超长文本切分）
- [x] 3.5 实现 JSON schema 验证
- [x] 3.6 保存提取结果到 `curriculum_kps.json`

**输出**: `edukg/data/output/curriculum_kps.json` ⚠️ 未生成（需要分步执行控制）

---

### 4. 知识图谱构建服务（阶段4）✅ 代码完成

**目标**: 为提取的知识点构建完整的知识图谱结构，输出符合 Neo4j 导入格式的 JSON 文件

> **状态**: 代码已完成，但 LLM 超时，未生成数据

#### 4.1 基础设施 ✅

- [x] 4.1.1 实现 `KGBuilder` 类，知识图谱构建主服务
- [x] 4.1.2 实现 `URIGenerator` 类，生成符合规范的 URI

#### 4.2 Class 提取 ✅ 代码完成

- [x] 4.2.1 实现 `ClassExtractor` 类
- [x] 4.2.2 实现 LLM 推断知识点类型
- [x] 4.2.3 生成 classes.json（格式符合Neo4j导入）

**输出**: `edukg/data/eduBureau/math/classes.json` ⚠️ 未生成

#### 4.3 Concept 提取 ✅ 代码完成

- [x] 4.3.1 实现 `ConceptExtractor` 类
- [x] 4.3.2 从知识点列表生成 Concept 实体
- [x] 4.3.3 添加 HAS_TYPE 关系（关联到Class）
- [x] 4.3.4 生成 concepts.json（格式符合Neo4j导入）

**输出**: `edukg/data/eduBureau/math/concepts.json` ⚠️ 未生成

#### 4.4 Statement 提取 ✅ 代码完成

- [x] 4.4.1 实现 `StatementExtractor` 类
- [x] 4.4.2 实现 LLM 生成知识点定义
- [x] 4.4.3 生成 statements.json（格式符合Neo4j导入）

**输出**: `edukg/data/eduBureau/math/statements.json` ⚠️ 未生成

#### 4.5 关系提取 ✅ 代码完成

- [x] 4.5.1 实现 `RelationExtractor` 类
- [x] 4.5.2 实现 LLM 分析知识点关系
- [x] 4.5.3 生成 relations.json（格式符合Neo4j导入）

**输出**: `edukg/data/eduBureau/math/relations.json` ⚠️ 未生成

---

### 5. 知识点对比服务（阶段5）✅ 已完成

**目标**: 对比课标知识点与 EduKG Concept

- [x] 5.1 实现 `ConceptComparator` 类，连接 Neo4j（只读）
- [x] 5.2 实现 `query_existing_concepts()` 查询所有 Concept label
- [x] 5.3 实现 `compare_knowledge_points()` 对比匹配状态
- [x] 5.4 实现 `generate_comparison_report()` 生成对比报告
- [x] 5.5 保存报告到 `kp_comparison_report.json`

**输出**: `edukg/data/output/kp_comparison_report.json` ⚠️ 未生成

---

## Part 2: 分步执行控制（使用 llmTaskLock）

> **背景**: Part 1 代码已完成，但 LLM 超时无法生成数据
> **目标**: 实现各步骤的断点续传，最后整合到 kg_main.py
> **基础设施**: 已完成 `edukg/core/llmTaskLock/` 模块（TaskState, CachedLLM, ProcessLock）

### 6. 步骤2增强 - 知识点提取分块（阶段6）

**目标**: 对 OCR 结果按 JSON 结构逐块提取，避免超时

- [x] 6.1 分析 `ocr_result.json` 结构，确定分块策略
  - 按 page 分块
  - 或按 content_requirement 分块
- [x] 6.2 修改 `kp_extraction.py`，每个分块作为 TaskState checkpoint
- [x] 6.3 实现分块级别的断点续传
- [x] 6.4 添加 `--resume` 参数，从断点恢复
- [x] 6.5 实现进度查询

**输出**: `state/step_2_kp_extraction.json`

---

### 7. 步骤3增强 - 类型推断分批（阶段7）✅ 已完成

**目标**: 对知识点列表分批推断类型，支持断点续传

- [x] 7.1 修改 `class_extractor.py`，使用 TaskState
- [x] 7.2 每批知识点作为一个 checkpoint
- [x] 7.3 使用 CachedLLM 缓存推断结果
- [x] 7.4 添加 `--resume` 参数
- [x] 7.5 实现进度查询

**输出**: `state/step_3_class_inference.json`

---

### 8. 步骤4增强 - Concept 生成（阶段8）✅ 已完成

**目标**: Concept 生成支持断点续传

- [x] 8.1 修改 `concept_extractor.py`，使用 TaskState
- [x] 8.2 每批 Concept 作为 checkpoint
- [x] 8.3 添加 `--resume` 参数
- [x] 8.4 实现进度查询

**输出**: `state/step_4_concept_gen.json`

---

### 9. 步骤5增强 - Statement 生成分批（阶段9）✅ 已完成

**目标**: Statement 定义生成分批处理，支持断点续传

- [x] 9.1 修改 `statement_extractor.py`，使用 TaskState
- [x] 9.2 每批 Statement 作为 checkpoint
- [x] 9.3 使用 CachedLLM 缓存定义生成结果
- [x] 9.4 添加 `--resume` 参数
- [x] 9.5 实现进度查询

**输出**: `state/step_5_statement_gen.json`

---

### 10. 步骤6增强 - 关系提取分批（阶段10）✅ 已完成

**目标**: 关系提取分批处理，支持断点续传

- [x] 10.1 修改 `relation_extractor.py`，使用 TaskState
- [x] 10.2 每批关系作为一个 checkpoint
- [x] 10.3 使用 CachedLLM 缓存关系分析结果
- [x] 10.4 添加 `--resume` 参数
- [x] 10.5 实现进度查询

**输出**: `state/step_6_relation_extract.json`

---

### 11. kg_main.py 增强（阶段11）

**目标**: 整合各步骤增强，支持分步执行和状态查询

> **前置条件**: 阶段6-10 已完成，各步骤模块已支持断点续传

- [ ] 11.1 添加 `--step` 参数，支持执行特定步骤（2-6）
- [ ] 11.2 添加 `--status` 参数，查询各步骤执行状态
- [ ] 11.3 整合各步骤的状态文件
  ```
  state/
  ├── step_2_kp_extraction.json
  ├── step_3_class_inference.json
  ├── step_4_concept_gen.json
  ├── step_5_statement_gen.json
  └── step_6_relation_extract.json
  ```
- [ ] 11.4 实现步骤依赖检查（步骤4依赖步骤3的输出）
- [ ] 11.5 添加进度显示和状态汇总

**使用示例：**
```bash
# 查看状态
python -m edukg.core.curriculum.kg_main --status

# 执行步骤2（知识点提取）
python -m edukg.core.curriculum.kg_main --step 2 --resume

# 执行步骤3（类型推断）
python -m edukg.core.curriculum.kg_main --step 3
```

---

### 12. 整合测试（阶段12）

**目标**: 验证完整的分步执行流程

- [ ] 12.1 测试 `--status` 参数
- [ ] 12.2 测试各步骤的 `--step` 和 `--resume` 参数
- [ ] 12.3 测试步骤依赖检查
- [ ] 12.4 验证断点续传功能
- [ ] 12.5 验证缓存功能
---

### Part 2 完成验证

**完成 Part 2 后，应生成以下数据文件：**

```bash
# 查看各步骤状态
python -m edukg.core.curriculum.kg_main --status

# 分步执行
python -m edukg.core.curriculum.kg_main --step 2 --resume
python -m edukg.core.curriculum.kg_main --step 3 --resume
python -m edukg.core.curriculum.kg_main --step 4 --resume
python -m edukg.core.curriculum.kg_main --step 5 --resume
python -m edukg.core.curriculum.kg_main --step 6 --resume

# 确认生成4个JSON文件
ls -la edukg/data/eduBureau/math/
# classes.json, concepts.json, statements.json, relations.json
```

---

## 里程碑：人工导入 Neo4j

**前置条件**: Part 2 完成，已生成4个JSON文件

完成 Part 2 后，使用现有导入脚本将知识图谱数据导入Neo4j：

```bash
# 使用现有导入脚本
python edukg/scripts/kg_data/import_kg.py \
  --classes edukg/data/eduBureau/math/classes.json \
  --concepts edukg/data/eduBureau/math/concepts.json \
  --statements edukg/data/eduBureau/math/statements.json \
  --relations edukg/data/eduBureau/math/relations.json
```

**导入后验证：**
```cypher
-- 查看新增的 Concept 数量
MATCH (c:Concept) WHERE c.uri CONTAINS "0.2" RETURN count(c)

-- 查看新增的 Statement 数量
MATCH (s:Statement) WHERE s.uri CONTAINS "0.2" RETURN count(s)
```

---

## Part 3: 教材知识点匹配

> **前提**: 里程碑完成，Neo4j 已包含小学知识点
> 此时教材匹配率会大幅提升

### 13. 教材解析服务（阶段13）

**目标**: 解析教材 JSON 文件，生成章节结构

- [ ] 13.1 创建 `edukg/core/textbook/` 目录结构
- [ ] 13.2 创建测试目录 `tests/textbook/`
- [ ] 13.3 实现 `TextbookParser` 类，解析教材 JSON 文件
- [ ] 13.4 实现 `parse_chapter()` 解析单个章节结构
- [ ] 13.5 保存解析结果到 `textbook_chapters.json`

**输出**: `edukg/data/output/textbook_chapters.json`

---

### 14. 知识点匹配服务（阶段14）

**目标**: 匹配教材知识点与 Neo4j Concept（补全后匹配率更高）

> **LLM使用**: 模糊匹配时使用LLM进行语义匹配

- [ ] 14.1 实现 `ConceptMatcher` 类，连接 Neo4j（只读）
- [ ] 14.2 实现 `query_all_concepts()` 查询所有 Concept label
- [ ] 14.3 实现 `exact_match()` 精确匹配（label 完全相同）
- [ ] 14.4 实现 `fuzzy_match()` 模糊匹配（LLM 语义匹配）
- [ ] 14.5 实现 `generate_matching_report()` 输出匹配报告
- [ ] 14.6 保存报告到 `matching_report.json`

**输出**: `edukg/data/output/matching_report.json`

---

## Part 4: 整合与文档

### 15. 主脚本整合（阶段15）

**目标**: 整合所有服务，提供命令行接口

- [ ] 15.1 创建 `edukg/core/curriculum/main.py` 整合课标模块
- [ ] 15.2 创建 `edukg/core/textbook/main.py` 整合教材模块
- [ ] 15.3 实现命令行参数（--skip-ocr, --debug）
- [ ] 15.4 实现错误处理和日志记录
- [ ] 15.5 验证完整流程

---

### 16. 文档（阶段16）

- [ ] 16.1 编写 README.md 记录使用方法
- [ ] 16.2 记录输出文件格式说明
- [ ] 16.3 验证数据质量

---

## 任务统计（更新版）

| Part | 阶段 | 任务数量 | 状态 | 说明 |
|------|------|----------|------|------|
| **Part 1** | 阶段1-5 | 31 | ✅ 代码完成 | ⚠️ 数据未生成 |
| **Part 2** | 阶段6-10 | 20 | ✅ 已完成 | 步骤2-6增强 |
| **Part 2** | 阶段11-12 | 12 | 待实现 | kg_main整合 + 测试 |
| **里程碑** | - | - | - | 人工导入 Neo4j |
| **Part 3** | 阶段13-14 | 11 | 待实现 | 教材匹配 |
| **Part 4** | 阶段15-16 | 8 | 待实现 | 整合文档 |
| **总计** | | **82** | **51 完成** | |

---

## 流程图

```
┌─────────────────────────────────────────────────────────────────┐
│  Part 1: 课标知识点提取（代码完成）                               │
│  ├── 阶段1: 项目初始化 ✅                                        │
│  ├── 阶段2: PDF OCR ✅ (已生成 ocr_result.json)                  │
│  ├── 阶段3: 知识点提取 ✅ 代码                                   │
│  ├── 阶段4: 知识图谱构建 ✅ 代码                                 │
│  └── 阶段5: 知识点对比 ✅ 代码                                   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  Part 2: 分步执行控制                                            │
│  ├── 阶段6: 步骤2增强（知识点提取分块）✅                         │
│  ├── 阶段7: 步骤3增强（类型推断分批）✅                           │
│  ├── 阶段8: 步骤4增强（Concept生成）✅                            │
│  ├── 阶段9: 步骤5增强（Statement生成分批）✅                       │
│  ├── 阶段10: 步骤6增强（关系提取分批）✅                           │
│  ├── 阶段11: kg_main.py增强（整合）                              │
│  └── 阶段12: 整合测试                                            │
│                                                                  │
│  输出: classes.json, concepts.json, statements.json, relations.json │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  里程碑: 人工导入 Neo4j                                          │
│  python edukg/scripts/kg_data/import_kg.py                      │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  Part 3: 教材知识点匹配（Neo4j 已有数据后）                       │
│  ├── 阶段13: 教材解析                                           │
│  └── 阶段14: 知识点匹配                                         │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  Part 4: 整合与文档                                              │
│  ├── 阶段15: 主脚本整合                                         │
│  └── 阶段16: 文档                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 使用示例

### Part 2 完成后（分步执行）

```bash
# 查看各步骤状态
python -m edukg.core.curriculum.kg_main --status

# 执行步骤2（知识点提取），从断点恢复
python -m edukg.core.curriculum.kg_main --step 2 --resume

# 执行步骤3（类型推断），从头开始
python -m edukg.core.curriculum.kg_main --step 3

# 执行步骤5（生成定义），清理旧缓存
python -m edukg.core.curriculum.kg_main --step 5 --clear-cache

# 执行完整流程（默认行为）
python -m edukg.core.curriculum.kg_main
```

### 里程碑完成后（导入 Neo4j）

```bash
# 导入数据到 Neo4j
python edukg/scripts/kg_data/import_kg.py \
  --classes edukg/data/eduBureau/math/classes.json \
  --concepts edukg/data/eduBureau/math/concepts.json \
  --statements edukg/data/eduBureau/math/statements.json \
  --relations edukg/data/eduBureau/math/relations.json
```

---

## LLM 使用说明

| 任务 | 是否需要LLM | LLM作用 | 模型 |
|------|-------------|---------|------|
| 知识点提取（阶段3）| ✅ 需要 | 从OCR文本中识别结构化知识点 | glm-4-flash |
| 类型判断（阶段4.2）| ✅ 需要 | 推断知识点属于哪个Class | glm-4-flash |
| Statement定义（阶段4.4）| ✅ 需要 | 生成知识点的定义描述 | glm-4-flash |
| 关系提取（阶段4.5）| ✅ 需要 | 分析知识点之间的关系 | glm-4-flash |
| 模糊匹配（阶段14）| ✅ 需要 | 语义匹配教材知识点 | glm-4-flash |

**成本说明**: glm-4-flash 是免费模型，无需担心API费用

---

## 输出文件说明

### Part 1 & Part 2 输出（课标知识点提取）

| 文件 | 阶段 | 说明 | 状态 |
|------|------|------|------|
| `edukg/data/eduBureau/math/ocr_result.json` | 阶段2 | OCR 识别结果 | ✅ 已生成 |
| `edukg/data/eduBureau/math/classes.json` | 阶段4/Part2 | Class 定义 | ⚠️ 待生成 |
| `edukg/data/eduBureau/math/concepts.json` | 阶段4/Part2 | Concept 知识点 | ⚠️ 待生成 |
| `edukg/data/eduBureau/math/statements.json` | 阶段4/Part2 | Statement 定义 | ⚠️ 待生成 |
| `edukg/data/eduBureau/math/relations.json` | 阶段4/Part2 | 关系 | ⚠️ 待生成 |
| `edukg/data/output/curriculum_kps.json` | 阶段3/Part2 | 课标知识点 | ⚠️ 待生成 |
| `edukg/data/output/kp_comparison_report.json` | 阶段5 | 对比报告 | ⚠️ 待生成 |

### Part 3 输出（教材知识点匹配）

| 文件 | 阶段 | 说明 |
|------|------|------|
| `edukg/data/output/textbook_chapters.json` | 阶段13 | 教材章节结构 |
| `edukg/data/output/matching_report.json` | 阶段14 | 匹配报告 |

---

## URI 命名规范

```
URI 格式: http://edukg.org/knowledge/{version}/{type}/math#{id}

┌─────────────────────────────────────────────────────────────────┐
│ version: 0.2 (我们自己设计的数据，区分 EduKG 的 0.1)              │
│ type: class | instance | statement                              │
│ id: {label_pinyin}-{md5(label)}                                  │
│                                                                  │
│ MD5生成代码:                                                      │
│ import hashlib                                                   │
│ md5_str = hashlib.md5(label.encode("utf-8")).hexdigest()         │
└─────────────────────────────────────────────────────────────────┘

示例:
- label: "小学数概念"
- pinyin: "xiaoxueshugainian"
- md5: hashlib.md5("小学数概念".encode("utf-8")).hexdigest()
- uri: "http://edukg.org/knowledge/0.2/class/math#xiaoxueshugainian-{md5}"
```

---

## 目录结构

```
edukg/core/
├── llmTaskLock/                  # 任务锁模块（已完成）
│   ├── state_manager.py          # TaskState 状态管理
│   ├── llm_cache.py              # CachedLLM 缓存
│   └── process_lock.py           # ProcessLock 进程锁
│
├── curriculum/                   # 课标模块
│   ├── __init__.py
│   ├── pdf_ocr.py               # 百度 OCR（收费）
│   ├── kp_extraction.py         # LLM 提取（免费）- 已集成 TaskState
│   ├── class_extractor.py       # 类型推断（LLM）- 已集成 CachedLLM
│   ├── concept_extractor.py     # Concept 生成
│   ├── statement_extractor.py   # 定义生成（LLM）- 已集成 CachedLLM
│   ├── relation_extractor.py    # 关系提取（LLM）
│   ├── kg_main.py               # 主脚本（待增强：--step, --status）
│   ├── kp_comparison.py         # 知识点对比
│   └── ttl_generator.py         # TTL 生成
│
└── textbook/                     # 教材模块（待实现）
    ├── __init__.py
    ├── parser.py                # 解析教材 JSON
    ├── matcher.py               # 匹配知识点
    └── main.py                  # 主脚本

tests/
├── curriculum/
│   ├── test_pdf_ocr.py
│   ├── test_kp_extraction.py
│   ├── test_kg_builder.py
│   ├── test_kp_comparison.py
│   └── test_main.py
│
├── textbook/
│   ├── test_parser.py
│   ├── test_matcher.py
│   └── test_main.py
│
└── test_llmTaskLock/            # llmTaskLock 测试（已完成）
    ├── test_state_manager.py
    ├── test_llm_cache.py
    └── test_process_lock.py
```