## Context

### 项目背景

知识图谱数据处理项目已完成数学学科的核心数据导入：
- **kg-neo4j-schema**：Neo4j schema 初始化（节点标签、唯一性约束）
- **kg-math-knowledge-points**：4,490 个知识点节点导入
- **kg-math-native-relations**：10,198 条原生关系导入（RELATED_TO, SUB_CATEGORY）
- **kg-infrastructure-init**：状态管理、成本监控基础设施
- **kg-math-prerequisite-inference**：前置关系推断（TEACHES_BEFORE, PREREQUISITE）

### 当前问题

**教材数据与知识点数据割裂**：

```
教材数据 (本地 JSON/TTL)          知识点数据 (SPARQL + Neo4j)
┌─────────────────────┐          ┌─────────────────────┐
│ 学段: 初中          │          │ uri: statement#1622 │
│ 年级: 七年级        │    ??    │ label: 正数的定义   │
│ 教材: 上册          │ ───────▶ │ type: 数学定义      │
│ 章节: 有理数        │          │ source: 1.1.1.1.1   │
│ 知识点: 正数和负数  │          │ relatedTo: 正实数   │
└─────────────────────┘          └─────────────────────┘
```

**名称不一致问题**：
- 教材：`正数和负数的概念` vs SPARQL：`正数的定义`
- 教材：`绝对值` vs SPARQL：`绝对值的定义`、`绝对值的性质`

### 约束条件

1. **LLM 成本控制**：使用免费模型（GLM-4-flash）进行语义匹配
2. **幂等性**：脚本可重复执行，不产生重复数据
3. **数据完整性**：匹配失败的教材知识点需要记录，不能丢失

## Goals / Non-Goals

**Goals:**
1. 将 24 册教材 JSON 数据导入 Neo4j（小学 12 册 + 初中 6 册 + 高中 6 册）
2. 建立 Chapter 与 KnowledgePoint 的映射关系
3. 使用 LLM 解决知识点名称不一致的匹配问题
4. 记录匹配置信度，支持后续人工审核

**Non-Goals:**
1. 不处理其他学科（仅数学）
2. 不推断新的前置关系（已在 kg-math-prerequisite-inference 处理）
3. 不修改已有的知识点节点数据

## Decisions

### D1: 使用 TextbookKnowledgePoint 中间节点

**问题**：教材知识点名称与 SPARQL 知识点名称不一致，直接关联会丢失信息。

**方案**：引入中间节点 `TextbookKnowledgePoint`

```
Chapter ──USES_KNOWLEDGE_POINT──▶ TextbookKnowledgePoint ──MAPPED_TO──▶ KnowledgePoint
                                         │
                                         ├── name: "正数和负数的概念"
                                         ├── confidence: 0.95
                                         └── match_method: "llm"
```

**优点**：
- 保留原始教材知识点名称
- 记录匹配置信度
- 支持一对多映射（一个教材知识点可能对应多个 SPARQL 知识点）

**替代方案**：直接在 KnowledgePoint 节点添加 `textbook_names` 属性
- **缺点**：无法记录置信度，无法支持一对多映射

### D2: 按章节批量 LLM 匹配

**问题**：教材有约 3,000 个知识点，逐个匹配 LLM 调用成本高。

**方案**：按章节批量匹配，每次 LLM 调用处理一个章节的所有知识点

```python
prompt = f"""
以下是教材章节"{chapter_name}"的知识点名称列表：
{kp_names_from_textbook}

以下是 Neo4j 中数学知识点的候选列表（按相似度筛选前 50 个）：
{kp_names_from_neo4j}

请为每个教材知识点匹配最合适的 Neo4j 知识点，并给出置信度（0-1）。
"""
```

**优点**：
- LLM 调用次数从 ~3,000 次减少到 ~300 次
- 章节上下文有助于提高匹配准确率

### D3: 匹配置信度阈值

**阈值设定**：
- ≥ 0.9：自动创建 MAPPED_TO 关系
- 0.7 - 0.9：标记为 `needs_review`
- < 0.7：标记为 `no_match`，输出到人工审核列表

### D4: 数据模型扩展

**新增节点类型**：

| 节点标签 | 属性 | 说明 |
|---------|------|------|
| Textbook | id, name, stage, grade, semester, publisher | 教材（如"七年级上册"） |
| Chapter | id, name, order, textbook_id | 章节（如"有理数"） |
| TextbookKnowledgePoint | id, name, chapter_id, matched_kp_id, confidence, status | 教材知识点 |

**新增关系类型**：

| 关系 | 起点 | 终点 | 说明 |
|------|------|------|------|
| HAS_CHAPTER | Textbook | Chapter | 教材包含章节 |
| USES_KNOWLEDGE_POINT | Chapter | TextbookKnowledgePoint | 章节使用知识点 |
| MAPPED_TO | TextbookKnowledgePoint | KnowledgePoint | 映射到 SPARQL 知识点 |

## Risks / Trade-offs

### R1: LLM 匹配准确率

**风险**：LLM 可能错误匹配知识点，影响知识图谱质量

**缓解措施**：
1. 使用置信度阈值筛选
2. 低置信度结果标记 `needs_review`
3. 输出匹配报告，支持人工审核

### R2: 数据覆盖不完整

**风险**：部分教材知识点无法匹配到 SPARQL 知识点

**缓解措施**：
1. 保留 TextbookKnowledgePoint 节点（即使未匹配）
2. 输出未匹配列表，支持后续补充 SPARQL 数据

### R3: LLM API 限流

**风险**：GLM-4-flash 免费 API 有调用频率限制

**缓解措施**：
1. 使用 kg-infrastructure-init 的 StateDB 支持断点续传
2. 添加调用间隔控制（每次调用后等待 1 秒）

## Migration Plan

1. **阶段 1**：导入教材结构数据（Textbook, Chapter 节点）
2. **阶段 2**：LLM 批量匹配知识点
3. **阶段 3**：导入匹配结果（TextbookKnowledgePoint 节点）
4. **阶段 4**：验证数据完整性

**回滚策略**：
- 每个阶段独立事务
- 失败时删除当前阶段创建的节点和关系

## Open Questions

1. **Q1**：是否需要支持教材版本差异（人教版 vs 苏教版）？
   - 当前仅处理人教版数据

2. **Q2**：是否需要定期更新 SPARQL 数据并重新匹配？
   - 当前设计为一次性导入，后续增量更新需要额外设计