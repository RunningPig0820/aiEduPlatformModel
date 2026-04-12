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

**设计方案（采纳 DeepSeek 建议）**:

采用 **向量检索方案** 作为粗筛机制，比 difflib 更精准：

| 方案 | 说明 | 语义理解 | 推荐 |
|------|------|---------|------|
| difflib | 字符相似度匹配 | 弱（"勾股定理" ≠ "毕达哥拉斯定理"） | ❌ |
| **向量检索** | Embedding语义匹配 | 强（自动理解同义词） | ✅ |

**向量检索技术选型**:
- 模型: `BAAI/bge-small-zh-v1.5`（中文小模型，内存 2-4GB）
- 索引: numpy 暴力搜索（图谱 ≤ 5000 条足够快）
- 依赖: `sentence-transformers`

**改进清单**:
- [x] 粗筛机制：先用向量检索筛选 top-20 候选，避免遍历所有图谱知识点
- [x] 精确匹配标准化：名称标准化 + 同义词映射（加法→加、加法运算）
- [x] 同义词完整词匹配：防止过度匹配（"加法交换律"不扩展为"加法"）
- [x] 异常处理：LLM调用失败继续下一个候选
- [x] 未匹配记录：输出所有知识点，增加 `matched` 字段
- [x] 进度回调修复：使用实际已完成数量而非循环索引

- [ ] 16.1 安装依赖：`pip install sentence-transformers numpy`
- [ ] 16.2 验证向量检索器初始化（首次需下载 300MB 模型）
- [ ] 16.3 加载 EduKG Concept 列表（从 Neo4j）
- [ ] 16.4 执行 `match_textbook_kp.py --resume`
- [ ] 16.5 调用向量检索 + LLM双模型投票执行匹配
- [ ] 16.6 输出 `matches_kg_relations.json`（含未匹配知识点）
- [ ] 16.7 统计匹配率和未匹配知识点
- [ ] 16.8 基于匹配结果修正知识点 topic（解决专题继承偏差问题）

**Task 16.8 说明**：
- 根据匹配的 EduKG Concept 的 Class 类型修正 TextbookKP 的 topic
- 规则映射：数学概念/数学运算 → 数与代数，几何图形/几何性质 → 图形与几何
- 解决 Task 14 遗留的"加法"等知识点 topic 继承偏差问题

**资源评估（8GB 内存）**:
- 模型内存: 2.5 GB
- 向量存储: ~10 MB
- 总计: 约 3.5 GB（完全可运行）

**回退机制**:
- 若 `sentence-transformers` 安装失败，自动回退到 difflib 粗筛

---

## Phase 5: 验证和导入（待执行）

### 17. 验证和手动导入

**前置条件**: Phase 4 完成

- [ ] 17.1 人工验证 JSON 数据质量
- [ ] 17.2 准备 Cypher 导入脚本模板
- [ ] 17.3 手动导入 Neo4j
- [ ] 17.4 验证导入结果