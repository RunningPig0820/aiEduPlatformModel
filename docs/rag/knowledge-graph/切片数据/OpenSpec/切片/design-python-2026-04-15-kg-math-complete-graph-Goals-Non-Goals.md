# Goals / Non-Goals

> summary: 目标：解析教材JSON、LLM推断补全缺失知识点、双模型匹配到EduKG Concept并输出关系；非目标：不直接导入Neo4j、不处理其他学科、不实现前置关系推断。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-Goals-Non-Goals.md
> 类别：项目介绍

---

### Goals / Non-Goals

> 检索摘要：目标：解析教材JSON、LLM推断补全缺失知识点、双模型匹配到EduKG Concept并输出关系；非目标：不直接导入Neo4j、不处理其他学科、不实现前置关系推断。

**Goals:**
1. 解析教材 JSON 数据，输出标准格式 JSON
2. LLM 推断补全缺失的教学知识点（小学3-6年级、初中、高中）
3. 使用双模型推理匹配教材知识点到 EduKG Concept
4. 输出所有关系数据（CONTAINS, IN_UNIT, MATCHES_KG）
5. 数据清洗：清理"通用"标签、规范 Section 标签
6. 知识点属性扩展：难度、重要性、认知维度、专题分类

**Non-Goals:**
1. 不直接导入 Neo4j（人工验证后手动导入）
2. 不处理其他学科（仅数学）
3. 不实现新的 LLM 推理机制（复用 kg-math-prerequisite-inference）
4. 不修改已有的 EduKG 节点数据
5. 不实现前置关系推断（由 kg-math-prerequisite-inference 负责）
6. 不实现多版本教材对比（未来迭代）

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§Goals / Non-Goals）
