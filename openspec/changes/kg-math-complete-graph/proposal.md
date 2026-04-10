> **执行顺序: 5/5** | **设计成本: 有** (LLM 调用) | **前置依赖: kg-math-prerequisite-inference**

## Why

知识图谱项目的**数据整合层**。前期 changes 已完成：
- kg-neo4j-schema：Neo4j schema 初始化
- kg-math-knowledge-points：EduKG 数据导入（Class 39, Concept 1,295, Statement 2,932）
- kg-math-native-relations：关系导入（RELATED_TO 10,183, SUB_CLASS_OF 38, PART_OF 298, BELONGS_TO 619）

**缺失的关键环节**：教材（课本）数据与知识点的关联。

当前问题：
1. **教材 JSON 数据未使用**：本地爬取的教师之家数据（小学/初中/高中 24册 JSON）包含章节和知识点名称，但未与 EduKG 知识点关联
2. **知识点归属缺失**：EduKG 知识点没有年级/教材信息，无法回答"某个知识点在哪个年级学习"
3. **教材-知识点映射困难**：两套数据的知识点名称不完全一致，精确匹配率仅 6%

**业务价值**：
- 支持"按年级/教材查询知识点"
- 支持"某章节包含哪些知识点"
- 支持"某知识点的学习路径"（从哪个年级开始学）

## What Changes

### 1. 教材数据生成模块 (`edukg/core/textbook/`)

```
edukg/core/textbook/
├── __init__.py
├── data_generator.py         # 教材数据生成器
├── uri_generator.py          # URI 生成逻辑 (v3.1)
├── kp_matcher.py             # 知识点匹配器（调用 llm_inference）
├── filters.py                # 知识点过滤规则
└── config.py                 # 配置
```

**核心能力**：
- `TextbookDataGenerator`: 教材数据生成器
- `URIGenerator`: URI 生成器（v3.1）
- `KPMatcher`: 知识点匹配器（复用 llm_inference）

### 2. 命令行入口 (`edukg/scripts/kg_data/`)

```
edukg/scripts/kg_data/
├── generate_textbook_data.py # 数据生成命令行入口
└── match_textbook_kp.py      # 知识点匹配命令行入口
```

### 3. 输出 JSON 文件（手动导入）

```
edukg/data/edukg/math/5_教材目录/output/
├── textbooks.json           # 教材节点（24册）
├── chapters.json            # 章节节点（~152章）
├── sections.json            # 小节节点（~500+）
├── textbook_kps.json        # 教材知识点节点（~346个）
├── contains_relations.json  # CONTAINS 关系
├── in_unit_relations.json   # IN_UNIT 关系
├── matches_kg_relations.json # MATCHES_KG 关系（推理结果）
└── import_summary.json      # 导入统计摘要
```

## Capabilities

### New Capabilities

- `textbook-data-generator`: 教材数据生成能力
- `textbook-uri-generator`: URI 生成能力（v3.1）
- `textbook-kp-matcher`: 教材-知识点匹配能力（复用双模型投票）

### Dependencies

- `edukg/core/llm_inference/`: 复用双模型投票机制

## Impact

- **新模块**: `edukg/core/textbook/`
- **新脚本**: `generate_textbook_data.py`, `match_textbook_kp.py`
- **输出文件**: JSON 格式，手动验证后导入 Neo4j
- **依赖**: 依赖 `kg-math-prerequisite-inference` 的 `llm_inference` 模块