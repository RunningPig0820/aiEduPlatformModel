# D1：多索引 + vector_type 必填路由

> summary: vector_type 必填多索引路由，映射放 Python Java 不感知 COS；未知 400/缺失 422，topic 本期建、question/rag 占位。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-question-type-mastery-python-D1-多索引-vector_type-必填路由.md
> 类别：架构设计

---

### D1：多索引 + vector_type 必填路由（不做单索引 filter）

> 检索摘要：vector_type 必填多索引路由，映射放 Python Java 不感知 COS；未知 400/缺失 422，topic 本期建、question/rag 占位。

后端「题目索引/题型索引/RAG 索引后面都要」——若用单索引 + metadata filter，将来切多索引要改契约。**本期就按多索引设计**：`vector_type` 是**必填**的逻辑类型，Python 经 `COS_VECTORS_INDEXES` 映射到物理索引。

```
vector_type (逻辑名)  → 物理索引 (COS)
  "topic"              →  topic-index     (本期建)
  "question"           →  question-index  (配置占位, 不建)
  "rag"                →  rag-index       (配置占位, 不建)
```

- **为什么必填而非缺省兜底**：用户拍板「每个查询由后端显式确定」。多索引下缺省语义模糊（不能跨索引全查，COS `query_vectors` 一次一个索引），必填最简单、可预期。
- **为什么映射放 Python**：Java 不感知 COS 基础设施（桥接哲学）；将来索引改名只动 Python 配置，不动 Java 契约。
- 未知 `vector_type` → 400；缺失 → 422（Pydantic 必填校验）。

> 证据：详见 `2.OpenSpec design 决策/design-python-question-type-mastery-python.md`（§D1）｜ 语雀-决策记录.md D13
