## Context

### 项目背景

知识图谱数据处理项目已完成数学学科的核心数据导入：
- Neo4j schema 初始化（节点标签、唯一性约束）
- EduKG 数据导入（Class 39, Concept 1,295, Statement 2,932）
- 关系导入（RELATED_TO 10,183, SUB_CLASS_OF 38, PART_OF 298, BELONGS_TO 619）

### 当前问题

**教材数据与知识点数据割裂**：

```
教材数据 (本地 JSON)              知识点数据 (Neo4j EduKG)
┌─────────────────────┐          ┌─────────────────────┐
│ 学段: 初中          │          │ uri: instance#1047  │
│ 年级: 七年级        │    ??    │ label: 余弦定理     │
│ 教材: 上册          │ ───────▶ │ type: 数学定理      │
│ 章节: 有理数        │          │ source: EduKG       │
│ 知识点: 正数和负数  │          │ relatedTo: 三角形   │
└─────────────────────┘          └─────────────────────┘
```

**名称不一致问题**：
- 教材：`正数和负数的概念` vs EduKG：`正数的定义`
- 精确匹配率仅 6% (24/346)

### 设计约束

1. **输出 JSON 文件**：不直接导入 Neo4j，由人工验证后手动导入
2. **两部分分离**：数据生成 + 推理
3. **复用双模型推理**：依赖 kg-math-prerequisite-inference 的 GLM-4-flash + DeepSeek 投票机制

## Goals / Non-Goals

**Goals:**
1. 解析教材 JSON 数据，输出标准格式 JSON
2. 生成教材-章节-小节-知识点层级结构数据
3. 使用双模型推理匹配教材知识点到 EduKG Concept
4. 输出所有关系数据（CONTAINS, IN_UNIT, MATCHES_KG）

**Non-Goals:**
1. 不直接导入 Neo4j（人工验证后手动导入）
2. 不处理其他学科（仅数学）
3. 不实现新的 LLM 推理机制（复用 kg-math-prerequisite-inference）
4. 不修改已有的 EduKG 节点数据

## Decisions

### D1: 两部分分离设计

**第一部分：数据生成**
- 输入：教材原始 JSON（edukg/data/textbook/math/renjiao/）
- 输出：标准化 JSON 文件
- 无 LLM 调用，纯数据转换

**第二部分：推理**
- 输入：数据生成输出的 JSON + Neo4j EduKG 数据
- 输出：匹配关系 JSON
- 使用双模型推理（依赖 kg-math-prerequisite-inference）

### D2: 输出文件结构

```
edukg/data/edukg/math/5_教材目录/
├── output/
│   ├── textbooks.json           # 教材节点
│   ├── chapters.json            # 章节节点
│   ├── sections.json            # 小节节点
│   ├── textbook_kps.json        # 教材知识点节点
│   ├── contains_relations.json  # CONTAINS 关系
│   ├── in_unit_relations.json   # IN_UNIT 关系
│   ├── matches_kg_relations.json # MATCHES_KG 关系（推理结果）
│   └── import_summary.json      # 导入统计摘要
```

### D3: 数据模型设计

**节点设计**：

| 节点类型 | 约束 | 属性 |
|---------|------|------|
| Textbook | `uri UNIQUE`, `id UNIQUE` | uri, id, label, stage, grade, semester, publisher, edition |
| Chapter | `uri UNIQUE`, `id UNIQUE` | uri, id, label, order |
| Section | `uri UNIQUE`, `id UNIQUE` | uri, id, label, order, mark |
| TextbookKP | `uri UNIQUE` | uri, label, stage, grade |

**关系设计（4 种）**：

| 关系类型 | 起点 → 终点 | 语义 |
|---------|------------|------|
| **CONTAINS** | Textbook → Chapter → Section | 目录层级 |
| **IN_UNIT** | TextbookKP → Section | 知识点所属单元 |
| **PREREQUISITE** | TextbookKP → TextbookKP/Concept | 先修关系 |
| **MATCHES_KG** | TextbookKP → Concept | 匹配图谱 |

### D4: URI 命名规范 (v3.1)

**基础格式**：
```
http://edukg.org/knowledge/3.1/{type}/math#{id}
```

**ID 编码规则**：

| 节点类型 | ID 格式 | 示例 |
|---------|--------|------|
| Textbook | `{publisher}-{grade}{semester}` | `renjiao-g1s` |
| Chapter | `{textbook_id}-{order}` | `renjiao-g1s-1` |
| Section | `{chapter_id}-{order}` | `renjiao-g1s-1-1` |
| TextbookKP | `textbook-{stage}-{seq:05d}` | `textbook-primary-00001` |

**年级编码**：小学 g1-g6, 初中 g7-g9, 高中 bixiu1-3

**学期编码**：上册→s, 下册→x, 高中无学期

### D5: 知识点过滤规则

```python
NON_KNOWLEDGE_POINT_MARKERS = {
    "数学活动", "小结", "整理和复习", "本章综合与测试",
    "本节综合与测试", "复习题", "★数学乐园", ...
}
```

### D6: 双模型推理复用

**复用 kg-math-prerequisite-inference 的机制**：

```python
# 投票规则
def vote_match(glm_result, deepseek_result):
    """两模型投票匹配"""
    if glm_result['is_match'] and deepseek_result['is_match']:
        confidence = min(glm_result['confidence'], deepseek_result['confidence'])
        return ('MATCHES_KG', confidence, 'llm_vote')
    elif glm_result['is_match'] or deepseek_result['is_match']:
        # 单模型通过，标记为候选
        return ('MATCHES_KG_CANDIDATE', confidence, 'llm_single')
    return None
```

**匹配阈值**：
- ≥ 0.9：MATCHES_KG
- 0.7 - 0.9：MATCHES_KG_CANDIDATE
- < 0.7：不匹配

## Risks / Trade-offs

### R1: 知识点匹配率低

**风险**：当前精确匹配率仅 6%

**缓解**：双模型推理提高匹配率，保留未匹配记录

### R2: 手动导入验证成本

**风险**：人工验证 JSON 数据需要时间

**缓解**：
- 输出详细的统计摘要
- 提供 Cypher 导入脚本模板
- 分批验证导入

### R3: 推理依赖

**风险**：依赖 kg-math-prerequisite-inference 的推理机制

**缓解**：kg-math-prerequisite-inference 需要先完成

## Migration Plan

**执行步骤**：

1. **数据生成**：
   - 运行 `generate_textbook_data.py`
   - 输出 textbooks.json, chapters.json, sections.json, textbook_kps.json
   - 输出 contains_relations.json, in_unit_relations.json

2. **人工验证**：
   - 检查输出文件数据质量
   - 验证节点数量、URI 格式、关系完整性

3. **手动导入**：
   - 执行约束创建 Cypher
   - 分批导入节点 JSON
   - 分批导入关系 JSON

4. **推理**：
   - 运行 `match_textbook_kp.py`
   - 输出 matches_kg_relations.json
   - 人工验证后导入

## Open Questions

1. **Q1**：是否需要先完成 kg-math-prerequisite-inference？
   - 是，推理部分依赖其双模型投票机制

2. **Q2**：JSON 导入脚本是否需要自动生成？
   - 可选，提供 Cypher 模板即可