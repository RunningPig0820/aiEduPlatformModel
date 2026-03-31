> **执行顺序: 6/6** | **设计成本: 有** (LLM 调用 ~500次) | **前置依赖: kg-math-prerequisite-inference**

## Why

知识图谱项目的**数据整合层**。前期 changes 已完成：
- kg-neo4j-schema：Neo4j schema 初始化
- kg-math-knowledge-points：知识点数据清洗和导入（来自 EduKG TTL）
- kg-math-native-relations：原生关系导入（relatedTo, subCategory）
- kg-infrastructure-init：状态管理、成本监控基础设施
- kg-math-prerequisite-inference：前置关系推断（TEACHES_BEFORE, PREREQUISITE）

**缺失的关键环节**：教材（课本）数据与知识点的关联。

当前问题：
1. **教材 JSON 数据未使用**：本地爬取的教师之家数据（小学/初中/高中 24册 JSON）包含章节和知识点名称，但未与 SPARQL 知识点关联
2. **知识点归属缺失**：SPARQL 知识点没有年级/教材信息，无法回答"某个知识点在哪个年级学习"
3. **教材-知识点映射困难**：两套数据的知识点名称不完全一致（如"正数和负数的概念" vs "正数的定义"），需要 LLM 语义匹配

**业务价值**：
- 支持"按年级/教材查询知识点"
- 支持"某章节包含哪些知识点"
- 支持"某知识点的学习路径"（从哪个年级开始学）

## What Changes

1. **教材数据解析脚本**
   - 解析小学/初中/高中 JSON 文件（24册）
   - 提取学段、年级、教材、章节、知识点名称
   - 输出标准化教材数据 JSON

2. **教材章节导入脚本**
   - 创建 Textbook 节点（24册）
   - 创建 Chapter 节点（约 300 个）
   - 创建 HAS_CHAPTER 关系

3. **LLM 教材-知识点匹配脚本**
   - 读取教材 JSON 中的知识点名称列表
   - 读取 Neo4j 中的知识点节点
   - 使用 LLM（GLM-4-flash）进行语义匹配
   - 生成 TextbookKnowledgePoint 中间节点（记录匹配置信度）
   - 输出匹配结果 CSV

4. **教材-知识点关联导入脚本**
   - 导入 TextbookKnowledgePoint 节点
   - 创建 USES_KNOWLEDGE_POINT 关系（Chapter → TextbookKnowledgePoint）
   - 创建 MAPPED_TO 关系（TextbookKnowledgePoint → KnowledgePoint）
   - 验证关联完整性

5. **数据验证脚本**
   - 验证教材章节覆盖率
   - 验证知识点关联率
   - 输出缺失报告

## Capabilities

### New Capabilities

- `textbook-data-parser`: 教材数据解析能力，支持小学/初中/高中 JSON 格式解析
- `textbook-chapter-importer`: 教材章节导入 Neo4j 能力，创建层级结构
- `llm-textbook-kp-matcher`: LLM 教材-知识点语义匹配能力，支持批量匹配和置信度评估
- `textbook-kp-linker`: 教材-知识点关联导入能力，创建映射关系

### Modified Capabilities

- `knowledge-graph-core`: 新增 TextbookKnowledgePoint 节点类型和关联关系

## Impact

- **新脚本**: `parse_textbook_json.py`, `import_textbook_chapters.py`, `match_textbook_kp_llm.py`, `link_textbook_kp.py`, `validate_textbook_coverage.py`
- **中间文件**: `textbook_data.json`, `textbook_kp_matches.csv`
- **Neo4j**: 新增约 24 个 Textbook 节点，300 个 Chapter 节点，约 3,000 个 TextbookKnowledgePoint 节点
- **LLM 调用**: 约 500 次（按章节批量匹配，每章节约 20 次）
- **依赖**: 依赖 kg-math-prerequisite-inference change 完成并测试通过