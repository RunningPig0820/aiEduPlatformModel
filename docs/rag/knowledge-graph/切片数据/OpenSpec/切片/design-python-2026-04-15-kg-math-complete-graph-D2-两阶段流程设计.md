# 两阶段流程设计

> summary: 两阶段流程：第一阶段无LLM的数据生成标准化JSON，第二阶段LLM增强推断知识点并匹配关系，支持断点续传。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D2-两阶段流程设计.md
> 类别：操作流程

---

### D2：两阶段流程设计

> 检索摘要：两阶段流程：第一阶段无LLM的数据生成标准化JSON，第二阶段LLM增强推断知识点并匹配关系，支持断点续传。

**第一阶段：数据生成（无 LLM）**
- 输入：教材原始 JSON
- 输出：标准化 JSON 文件
- 过滤非知识点标记

**第二阶段：LLM 增强**
- 输入：第一阶段输出 + Neo4j EduKG 数据
- 输出：推断的教学知识点 + 匹配关系
- 支持断点续传

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D2：两阶段流程设计）
