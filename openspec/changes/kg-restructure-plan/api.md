# 知识图谱重构规划 API 接口文档

> 本 Change 不新增 API，仅更新现有 changes 的设计。

---

## 变更摘要

### 执行顺序变更

| Change | 原顺序 | 新顺序 |
|--------|--------|--------|
| kg-neo4j-schema | 1/5 | 1/5（无变化） |
| kg-math-knowledge-points | 2/5 | 2/5（增加教材导入） |
| kg-math-native-relations | 3/5 | 3/5（无变化） |
| kg-infrastructure-init | 4/5 | 4/5（无变化） |
| kg-math-prerequisite-inference | 5/5 | 5/5（无变化） |
| kg-math-complete-graph | 6/5 | 删除（合并到 kg-math-knowledge-points） |

### Schema 变更

| 节点/关系 | 操作 | 说明 |
|----------|------|------|
| TextbookKnowledgePoint | 新增 | 教材知识点中间节点 |
| USES_KNOWLEDGE_POINT | 新增 | Chapter → TextbookKnowledgePoint |
| MAPPED_TO | 新增 | TextbookKnowledgePoint → KnowledgePoint |

### kg-math-knowledge-points 能力扩展

| 能力 | 操作 | 说明 |
|------|------|------|
| textbook-json-parser | 新增 | 解析本地教材 JSON 数据 |
| llm-kp-matcher | 新增 | LLM 语义匹配教材知识点与 SPARQL 知识点 |

---

*文档生成时间: 2026-03-31*