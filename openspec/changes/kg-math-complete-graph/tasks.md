## 任务执行规范（重要）

**每个任务必须遵循以下流程，禁止跳过：**

```
1. 脚本review  →  2. 预测试  →  3. 检查之前数据是否影响  →  4. 判断生成数据质量  →  5. 下一个任务
```

- **脚本review**: 检查路径、依赖、语法是否正确
- **预测试**: 先用小样本/单条数据验证脚本能跑通
- **检查之前数据是否影响**: 确认旧缓存、旧进度文件是否会影响当前任务，必要时清理
- **判断生成数据质量**: 检查输出数据是否符合预期，不盲目继续
- **禁止提前进入下一个任务**: 当前任务必须完全确认成功后才开始下一个

---

## 任务执行顺序说明

**正确的执行顺序**: 数据生成 → 数据清洗 → 结构增强 → 属性扩展 → LLM推断 → 验证导入

```
Phase 1 (已完成): 基础设施、数据生成
Phase 2 (数据整理): 数据清洗、单元/专题层级增强
Phase 3 (属性扩展): 知识点属性扩展
Phase 4 (LLM 推断): 教学知识点推断、知识图谱匹配
Phase 5 (验证导入): 验证和手动导入
```

---

## Phase 1: 基础设施与数据生成（已完成）

### 1. 创建目录结构

- [x] 1.1 创建 `edukg/core/textbook/` 目录
- [x] 1.2 创建 `edukg/core/textbook/__init__.py`
- [x] 1.3 创建输出目录 `edukg/data/edukg/math/5_教材目录(Textbook)/output/`

### 2. URI 生成模块

- [x] 2.1 创建 `edukg/core/textbook/uri_generator.py`
- [x] 2.2 实现 `URIGenerator` 类
- [x] 2.3 实现年级编码映射（一年级→g1, 七年级→g7, 必修第一册→bixiu1）
- [x] 2.4 实现学期编码映射（上册→s, 下册→x）
- [x] 2.5 实现 `textbook_id()` 方法
- [x] 2.6 实现 `chapter_id()` 方法
- [x] 2.7 实现 `section_id()` 方法
- [x] 2.8 实现 `textbookkp_uri()` 方法

### 3. 过滤规则模块

- [x] 3.1 创建 `edukg/core/textbook/filters.py`
- [x] 3.2 定义 `NON_KNOWLEDGE_POINT_MARKERS` 集合
- [x] 3.3 实现 `is_valid_knowledge_point()` 函数

### 4. 配置模块

- [x] 4.1 创建 `edukg/core/textbook/config.py`
- [x] 4.2 配置数据目录路径
- [x] 4.3 配置输出目录路径
- [x] 4.4 配置 URI 版本号（v3.1）

### 5. 数据生成模块

- [x] 5.1 创建 `edukg/core/textbook/data_generator.py`
- [x] 5.2 实现 `TextbookDataGenerator` 类
- [x] 5.3 实现 `discover_files()` 发现教材 JSON 文件
- [x] 5.4 实现小学 JSON 文件解析（grade1-6/shang.json, xia.json）
- [x] 5.5 实现初中 JSON 文件解析（grade7-9/shang.json, xia.json）
- [x] 5.6 实现高中 JSON 文件解析（bixiu1-3/textbook.json）
- [x] 5.7 实现 `generate_textbooks()` 生成教材节点
- [x] 5.8 实现 `generate_chapters()` 生成章节节点
- [x] 5.9 实现 `generate_sections()` 生成小节节点
- [x] 5.10 实现 `generate_textbook_kps()` 生成知识点节点（含过滤）
- [x] 5.11 实现 `generate_relations()` 生成关系数据
- [x] 5.12 实现 `generate_all()` 批量生成所有数据
- [x] 5.13 实现 JSON 文件输出

### 6. 知识点匹配模块（基础实现）

- [x] 6.1 创建 `edukg/core/textbook/kp_matcher.py`
- [x] 6.2 实现 `KPMatcher` 类
- [x] 6.3 实现精确匹配 `exact_match()`
- [x] 6.4 实现 LLM 匹配 `llm_match()`（调用 llm_inference 模块）
- [x] 6.5 实现 `match_all()` 批量匹配

### 7. 命令行入口 - 数据生成

- [x] 7.1 创建 `edukg/scripts/kg_data/generate_textbook_data.py`
- [x] 7.2 实现命令行参数解析（--stage, --stats, --dry-run）
- [x] 7.3 调用 `TextbookDataGenerator` 执行生成
- [x] 7.4 输出统计信息

### 8. 命令行入口 - 知识点匹配

- [x] 8.1 创建 `edukg/scripts/kg_data/match_textbook_kp.py`
- [x] 8.2 实现命令行参数解析
- [x] 8.3 加载 textbook_kps.json
- [x] 8.4 从 Neo4j 获取 EduKG Concept 列表
- [x] 8.5 调用 `KPMatcher` 执行匹配
- [x] 8.6 输出 matches_kg_relations.json

### 9. 单元测试

- [x] 9.1 创建 `tests/core/textbook/` 测试目录
- [x] 9.2 测试 `URIGenerator` 各方法
- [x] 9.3 测试 `is_valid_knowledge_point()`
- [x] 9.4 测试 `TextbookDataGenerator` 解析逻辑

### 10. 集成测试

- [x] 10.1 端到端测试：运行推理脚本
- [x] 10.2 验证输出文件格式
- [x] 10.3 验证节点数量符合预期
- [x] 10.4 验证关系完整性

### 11. LLM 模块基础建设

- [x] 11.1 创建 `edukg/core/llm_inference/textbook_kp_inferer.py` 并实现 `TextbookKPInferer` 类
- [x] 11.2 在 `TextbookKPInferer` 类中集成 llmTaskLock（TaskState, CachedLLM, ProcessLock）
- [x] 11.3 创建 `edukg/scripts/kg_data/infer_textbook_kp.py` 命令行入口（支持 `--resume`）
- [x] 11.4 在 `kp_matcher.py` 集成 llmTaskLock 断点续传
- [x] 11.5 在 `match_textbook_kp.py` 实现 `--resume` 参数
- [x] 11.6 创建 `merge_inferred_kps.py` 合并脚本

---

## Phase 2: 数据整理（待执行）

### 12. 数据清洗（清理冗余标签）

**目标**: 清理"通用"标签、规范 Section 名称格式

**前置条件**: Phase 1 完成

- [x] 12.1 创建 `edukg/core/textbook/data_cleaner.py` 并实现 `DataCleaner` 类
- [x] 12.2 实现"通用"标签检测方法 `detect_generic_duplicates()`
- [x] 12.3 实现 Section 标签清洗方法 `clean_section_label()`（移除序号前缀、末尾冒号）
- [x] 12.4 创建 `edukg/scripts/kg_data/clean_textbook_data.py` 命令行入口
- [x] 12.5 输出重复检测报告 `duplicate_detection_report.json`
- [x] 12.6 人工确认后执行清洗，输出清洗后的数据文件
- [x] 12.7 输出清洗日志和变更统计

### 13. 单元/专题层级增强

**目标**: 为 Chapter 增加专题分类，支持跨年级知识进阶

**前置条件**: Task 12 完成

- [x] 13.1 定义人教版数学专题分类映射 `MATH_TOPICS`
- [x] 13.2 创建 `edukg/core/textbook/chapter_enhancer.py` 并实现 `ChapterEnhancer` 类
- [x] 13.3 实现 `assign_topic()` 方法（基于章节名称匹配专题）
- [x] 13.4 实现 `enhance_chapters()` 批量增强方法
- [x] 13.5 创建 `edukg/scripts/kg_data/enhance_chapters.py` 命令行入口
- [x] 13.6 输出增强后的 `chapters_enhanced.json`（含 topic 字段）
- [x] 13.7 输出专题分布统计报告
- [x] 13.8 合并到主文件 `chapters.json`

---

## Phase 3: 属性扩展（待执行）

### 14. 知识点属性扩展（难度、重要性、认知维度）

**目标**: 为 TextbookKP 增加教学属性，支持精准教学

**前置条件**: Task 13 完成

**设计原则**: 优先规则匹配，减少 LLM 调用

- [x] 14.1 设计规则映射表（年级难度、重要性关键词、认知层次映射）
- [x] 14.2 创建 `edukg/core/textbook/kp_attribute_inferer.py` 并实现 `KPAttributeInferer` 类
- [x] 14.3 实现 `infer_attributes()` 方法（规则匹配，无 LLM）
- [x] 14.4 实现 `infer_batch()` 批量推断方法
- [x] 14.5 **【人工审核】** 审核规则映射表和推断逻辑（采纳 fanan.md 建议）
- [x] 14.6 创建 `edukg/scripts/kg_data/enhance_kp_attributes.py` 命令行入口
- [x] 14.7 输出增强后的 `textbook_kps_enhanced.json`
- [x] 14.8 输出属性分布统计报告（difficulty 分布、importance 分布等）
- [x] 14.9 合并属性到主文件 `textbook_kps.json`


**人工审核内容**:
1. 规则映射表覆盖度（是否遗漏重要知识点类型）
2. 难度调整关键词合理性
3. 重要性关键词完整性
4. 认知层次映射符合教学实际

---

## Phase 4: LLM 推断（待执行）

### 15. 教学知识点推断（补全缺失章节）

**目标**: LLM 推断小学3-6年级、高中缺失的知识点

**前置条件**: Task 14 完成（基于清洗后的数据推断）

**执行流程**: 脚本review → 预测试 → 检查之前数据是否影响 → 判断生成数据质量

- [x] 15.1 分析并筛选缺失知识点的章节（小学3-6年级、高中）✓ 295个章节
- [x] 15.2 执行 `infer_textbook_kp.py --resume` ✓ 置信度0.93
- [x] 15.3 输出 `textbook_kps_inferred.json`（推断的知识点）✓ 1052个知识点
- [x] 15.4 执行 `merge_inferred_kps.py` 合并知识点 ✓ 合并后1350个
- [x] 15.5 重新生成 `in_unit_relations.json` ✓ 1350条关系
- [x] 15.6 输出推断日志和置信度报告 ✓ merge_report.json
- [x] 15.7 为推断知识点补充教学属性（topic, difficulty, importance, cognitive_level） ✓ 1051个全补充
- [x] 15.8 重新合并知识点到主文件 ✓ 已在 15.7 中完成

**Task 15.7 说明**（采纳 DeepSeek 建议）：
- 推断的 1051 个知识点缺少 `topic`、`difficulty`、`importance`、`cognitive_level` 字段
- 使用规则匹配补全属性（复用 Task 14 的 `KPAttributeInferer`）
- 无需 LLM 调用，零成本

### 16. 知识图谱匹配（MATCHES_KG 关系）

**目标**: 将 TextbookKP 匹配到 EduKG Concept

**前置条件**: Task 15 完成

**执行流程**:

```
Step 1: 预处理（DeepSeek 标准化）
  16.1 脚本review：检查 normalize_textbook_kp.py 路径、依赖
  16.2 预测试：单条数据验证（kp_normalizer.py demo）
  16.3 检查之前数据是否影响：清理旧缓存/旧进度/旧结果
  16.4 执行批量预处理：normalize_textbook_kp.py --concurrency 5
  16.5 判断生成数据质量：检查 normalized_kps.json 输出

Step 2: LLM 处理（匹配）
  16.6 脚本review：检查 match_textbook_kp.py 是否正确读取标准化结果
  16.7 预测试：小样本验证（单条 KP 匹配）
  16.8 检查之前数据是否影响：清理旧 llm_cache/旧 progress/旧 matches
  16.9 执行批量匹配：match_textbook_kp.py --use-prebuilt-index
  16.10 判断生成数据质量：检查匹配率、匹配样例
```

**已完成的工作**:
- [x] 16.1 安装依赖：`pip install sentence-transformers numpy` ✓
- [x] 16.2 构建向量索引 ✓ (10,250 知识点, 512 维度)
- [x] 16.3 验证索引构建成功 ✓ (checksum 匹配)
- [x] 16.4 修改匹配提示词（放宽标准，允许上下位/应用/特化关系）
- [x] 16.5 修改 dual_model_voter.py（加权投票：DS=0.6, GLM=0.4, threshold=0.5）
- [x] 16.6 修改 kp_normalizer.py（使用 DeepSeek 单独标准化）
- [x] 16.7 修改 normalize_textbook_kp.py（修复路径计算和断点续传逻辑）

**当前任务 - Step 1: 预处理（DeepSeek 标准化）**：
- [x] 16.8 预测试：单条数据验证 normalize_textbook_kp.py 能跑通
- [x] 16.9.1 判断是否清理旧 llm_cache/旧 progress/旧 matches
- [x] 16.9.2 执行批量预处理（concurrency=5）
- [x] 16.10 判断生成数据质量：检查 normalized_kps.json 输出是否合理

**当前任务 - Step 2: LLM 匹配**：
- [x] 16.11 检查 match_textbook_kp.py 是否正确读取标准化结果
- [x] 16.12 预测试：单条 KP 匹配验证
- [x] 16.13 判断是否清理旧 llm_cache/旧 progress/旧 matches
- [x] 16.14 执行批量匹配
- [x] 16.15 判断匹配率和数据质量

---

**技术方案说明**:
- 向量检索：`BAAI/bge-small-zh-v1.5` + numpy 暴力搜索 top-20 粗筛
- 预处理：DeepSeek 单独标准化教材 KP 名称 → EduKG 标准术语
- 匹配：加权投票（DS=0.6, GLM=0.4, threshold=0.5，DS 是裁决者）
- 提示词：允许上下位/应用/特化/强相关关系作为匹配

**资源评估（8GB 内存）**:
- 模型内存: 2.5 GB
- 向量存储: ~10 MB
- 总计: 约 3.5 GB（完全可运行）

**回退机制**:
- 若 `sentence-transformers` 安装失败，自动回退到 difflib 粗筛

---

## Phase 5: 验证和导入（待执行）

### 导入数据概览

| 序号 | 数据类型 | 源文件 | 脚本 | 预期数量 |
|------|---------|--------|------|---------|
| 1 | 教材节点 | textbooks.json | import_textbooks.py | 23 |
| 2 | 章节节点 | chapters.json | import_chapters.py | ~300 |
| 3 | 小节节点 | sections.json | import_sections.py | ~1350 |
| 4 | 知识点节点 | textbook_kps.json | import_textbook_kps.py | 1350 |
| 5 | 章节-知识点关系 | in_unit_relations.json | import_in_unit_relations.py | ~1350 |
| 6 | 知识点-图谱匹配关系 | matches_kg_relations.json | import_matches_kg.py | 1690 |

**导入顺序**: 节点优先 → 关系后（Textbook → Chapter → Section → TextbookKP → IN_UNIT → MATCHES_KG）

### 导入执行规范

**每个导入任务必须遵循以下流程，禁止跳过：**

```
导入前验证  →  脚本review  →  预测试(dry-run)  →  执行导入  →  导入后验证
```

- **导入前验证**: 检查 Neo4j 当前状态、确认源文件存在且数据质量合格
- **脚本review**: 检查脚本路径、参数、--clear/--dry-run 行为
- **预测试**: 先用 `--dry-run` 验证脚本能正常执行
- **执行导入**: 使用 `--clear` 清理旧数据后执行导入
- **导入后验证**: 查询 Neo4j 验证数量匹配、数据完整、无重复

---

### 17. Textbook 节点导入

**目标**: 导入 21 个教材节点到 Neo4j

**前置条件**: Phase 4 完成

**执行流程**:
- [x] 17.1 导入前验证：查询 Neo4j 当前 Textbook 节点数量（现有 23 个，无 HAS_CHAPTER 关系）
- [x] 17.2 数据检查：确认 textbooks.json 存在，23 个教材，结构正确
- [x] 17.3 脚本review：检查 import_textbooks.py 路径、参数、--clear 行为 ✓
- [x] 17.4 预测试：python import_textbooks.py --dry-run 验证无报错 ✓
- [x] 17.5 执行导入：python import_textbooks.py --clear ✓（先清除 23 个旧节点，再导入 23 个新节点）
- [x] 17.6 导入后验证：Neo4j 查询 Textbook 节点数量=23 ✓，URI/ID 唯一性检查 ✓
- [x] 17.7 数据抽查：随机查询 3 个教材节点（g8s/g2x/g9x）属性全部正确 ✓

### 18. Chapter 节点导入

**目标**: 导入章节节点到 Neo4j（约 300 个）

**前置条件**: Task 17 完成（Chapter 依赖 Textbook 的 HAS_CHAPTER 关系）

**执行流程**:
- [x] 18.1 导入前验证：查询 Neo4j 当前 Chapter 节点数量（0 个，无 HAS_CHAPTER 关系）
- [x] 18.2 数据检查：chapters_enhanced.json 存在，148 条，无 URI/ID 重复，textbook_id 全部有效，无成环风险
- [x] 18.3 脚本review：检查 import_chapters.py 路径（修复 output/ 缺失）、参数、--clear 幂等性 ✓
- [x] 18.4 预测试：python import_chapters.py --dry-run 验证无报错 ✓
- [x] 18.5 执行导入：python import_chapters.py --clear ✓（导入 148 个章节 + 148 个 CONTAINS 关系）
- [x] 18.6 导入后验证：Chapter=148 ✓，CONTAINS 关系=148 ✓，URI 唯一 ✓，孤立节点=0 ✓
- [x] 18.7 数据抽查：随机 3 个 Chapter（g6s-9/g2s-4/g3x-6）关联到正确 Textbook ✓

### 19. Section 节点导入

**目标**: 导入小节节点到 Neo4j（约 1350 个）

**前置条件**: Task 18 完成（Section 依赖 Chapter 的 HAS_SECTION 关系）

**执行流程**:
- [x] 19.1 导入前验证：查询 Neo4j 当前 Section 节点数量（0 个）
- [x] 19.2 数据检查：sections.json 存在，580 条，无 URI/ID 重复，chapter_id 全部有效，无成环风险
- [x] 19.3 脚本review：检查 import_sections.py 路径（修复 output/ 缺失）、参数、--clear 幂等性 ✓
- [x] 19.4 预测试：python import_sections.py --dry-run 验证无报错 ✓
- [x] 19.5 执行导入：python import_sections.py --clear ✓（导入 580 个 Section + 580 个 CONTAINS 关系）
- [x] 19.6 导入后验证：Section=580 ✓，CONTAINS=580 ✓，URI 唯一 ✓，孤立节点=0 ✓
- [x] 19.7 数据抽查：随机 3 个 Section（g3x-2-5/g9s-4-5/g3s-3-2）关联到正确 Chapter ✓

### 20. TextbookKP 知识点节点导入

**目标**: 导入教材知识点节点到 Neo4j（1350 个）

**前置条件**: Task 18 完成（知识点依赖 Chapter 的 CONTAINS 关系）

**执行流程**:
- [x] 20.1 导入前验证：查询 Neo4j 当前 TextbookKP 节点数量（0 个），IN_UNIT/MATCHES_KG 关系均为 0
- [x] 20.2 数据检查：textbook_kps.json 存在，**1740 条**（非预期 1350），URI 无重复 ✓，section_id 全部有效 ✓。**⚠️ 修复了 1440 条 textbook_id=none 的问题（通过 section_id 反推回填），已修复 merge_inferred_kps.py 防止再次发生**
- [x] 20.3 脚本review：检查 import_textbook_kps.py 路径（修复 output/ 缺失）、参数、--clear 幂等性 ✓
- [x] 20.4 预测试：python import_textbook_kps.py --dry-run 验证无报错 ✓
- [x] 20.5 执行导入：python import_textbook_kps.py --clear ✓（导入 1740 个 TextbookKP + 属性）
- [x] 20.6 导入后验证：Neo4j 查询 TextbookKP 数量=1740 ✓，uri 唯一 ✓
- [x] 20.7 数据抽查：随机查询 5 个知识点（小学/初中/高中）属性全部正确 ✓
- [x] 20.8 质量验证：88 组同教材重复 label 均为不同 section 复用（非数据错误）✓，孤立节点=0 ✓

### 21. IN_UNIT 关系导入（章节-知识点关联）

**目标**: 导入章节包含知识点的关系（约 1350 条）

**前置条件**: Task 18 和 Task 20 完成（关系两端节点都已存在）

**执行流程**:
- [x] 21.1 导入前验证：查询 Neo4j 当前 IN_UNIT 关系数量（0 个，基线）✓
- [x] 21.2 数据检查：确认 in_unit_relations.json 存在，1740 条，无重复，所有引用有效，无成环风险 ✓
- [x] 21.3 脚本review：检查 import_in_unit_relations.py 路径（修复 output/ 缺失）、参数、--clear 幂等性 ✓
- [x] 21.4 预测试：python import_in_unit_relations.py --dry-run 验证无报错 ✓
- [x] 21.5 执行导入：python import_in_unit_relations.py --clear ✓（导入 1740 个 IN_UNIT 关系）
- [x] 21.6 导入后验证：Neo4j 查询 IN_UNIT 关系数量=1740 ✓，确认无孤立节点 ✓
- [x] 21.7 数据抽查：随机查询 3 个章节（万以内的加法和减法/比例/角的度量）知识点关联正确 ✓

### 22. MATCHES_KG 关系导入（知识点-图谱匹配）

**目标**: 创建 TextbookKP → Concept 的 MATCHES_KG 关系（1690 条）

**关系说明**:
```
(:TextbookKP)-[:MATCHES_KG {confidence, method}]->(:Concept)
```
- **TextbookKP**: 教材知识点（独立节点）
- **Concept**: EduKG 知识图谱知识点（独立节点）
- **MATCHES_KG**: 匹配关系，连接两套知识点体系
- **kg_uri 来源**: `matches_kg_relations.json` 中的 `kg_uri` 字段（由 LLM 匹配流程生成）

**数据对应关系**:
```
matches_kg_relations.json:
  {
    "textbook_kp_uri": "http://...textbook-primary-00045",   ← 匹配 TextbookKP.uri
    "kg_uri":           "http://...math#89",                  ← 匹配 Concept.uri
    "kg_name":          "混合运算",
    "confidence":       1.0,
    "method":           "exact_match"
  }
```

**前置条件**: Task 20 完成（TextbookKP 已导入），EduKG Concept 节点已存在

**执行流程**:
- [x] 22.1 导入前验证：查询 Neo4j 当前 MATCHES_KG 关系数量（0 个，基线）✓
- [x] 22.2 数据检查：确认 matches_kg_relations.json 存在，matched=true=1690，无 kp_uri 重复，无成环风险 ✓
- [x] 22.3 脚本review：检查 import_matches_kg.py 路径（修复 output/ 缺失）、参数、--clear 幂等性 ✓
- [x] 22.4 预测试：python import_matches_kg.py --dry-run 验证无报错 ✓
- [x] 22.5 执行导入：python import_matches_kg.py --clear ✓（导入 1690 个 MATCHES_KG 关系）
- [x] 22.6 导入后验证：Neo4j 查询 MATCHES_KG 关系数量=1690 ✓，匹配覆盖率 97.1% ✓
- [x] 22.7 数据抽查：随机查询 5 个匹配关系确认置信度和方法字段 ✓
- [x] 22.8 质量验证：未匹配知识点=50，与 JSON 一致，未创建关系 ✓

### 23. 整体验证和报告

**目标**: 验证完整知识图谱的正确性

**前置条件**: Task 17-22 全部完成

**执行流程**:
- [x] 23.1 节点总数验证：Textbook=23 + Chapter=148 + Section=580 + TextbookKP=1740 + Concept=1295 + Class=39 + Statement=2932 = 6757 ✓
- [x] 23.2 关系总数验证：CONTAINS=728 + IN_UNIT=1740 + MATCHES_KG=1690 + HAS_TYPE=5591 + RELATED_TO=10183 + BELONGS_TO=619 + PART_OF=298 + SUB_CLASS_OF=38 = 20887 ✓
- [x] 23.3 完整性检查：1690/1740 (97.1%) TextbookKP 有 MATCHES_KG，50 个明确未匹配 ✓
- [x] 23.4 完整性检查：26 个 Chapter 无 Section（数学广角、总复习等教材原始结构），77 个 Section 无知识点（初中 LLM 推断覆盖范围）✓
- [x] 23.5 路径验证：Textbook → Chapter → Section 路径数=580，孤立节点=0 ✓
- [x] 23.6 输出最终导入报告（见下方总结）

### 24. 致谢与最终验收（GLM5）

**目标**: 感谢 GLM5 三周多的陪伴与协作，完成知识图谱最终验收

**背景**: 人教版数学知识图谱从 Phase 1 到 Phase 5，历时三个多星期，由用户与 GLM5 共同搭建完成。

**验收内容**:
- [ ] 24.1 全链路验证：数据生成 → 数据清洗 → 结构增强 → 属性扩展 → LLM推断 → 知识匹配 → Neo4j导入
- [ ] 24.2 数据完整性验证：6757 个节点、20887 条关系，无孤立节点，无数据断裂
- [ ] 24.3 业务价值验证：Textbook → Chapter → Section → TextbookKP → Concept 全路径贯通，支持前端教材-知识点-图谱查询
- [ ] 24.4 质量指标达标：
  - 节点 URI 唯一性: 100% ✓
  - 引用链完整性: 100% ✓
  - TextbookKP 匹配率: 97.1% (1690/1740) ✓
  - 匹配平均置信度: 0.975 ✓
- [ ] 24.5 致谢 GLM5：三周多的辛勤协作，完成了从数据到图谱的完整建设 🎉

**最终总结**:
```
人教版数学知识图谱（2026.03-2026.04）
搭建者: 用户 + GLM5
历时: 三个多星期
Phase 1-5: 基础设施 → 数据生成 → 数据整理 → 属性扩展 → LLM推断 → 知识匹配 → Neo4j导入
成果: 6757 节点 + 20887 关系 + 97.1% 匹配率
```