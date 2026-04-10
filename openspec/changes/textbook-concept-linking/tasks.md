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