# Context：设计约束

> summary: 本阶段不直接导入Neo4j，输出JSON由人工验证后手动导入；核心代码进edukg/core，复用双模型推理并全链路支持llmTaskLock断点续传。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-Context-设计约束.md
> 类别：架构设计

---

### Context：设计约束

> 检索摘要：本阶段不直接导入Neo4j，输出JSON由人工验证后手动导入；核心代码进edukg/core，复用双模型推理并全链路支持llmTaskLock断点续传。

1. **输出 JSON 文件**：不直接导入 Neo4j，由人工验证后手动导入
2. **核心代码放入 edukg/core**：scripts 只做命令行入口
3. **复用双模型推理**：依赖 kg-math-prerequisite-inference 的投票机制
4. **所有 LLM 任务支持断点续传**：使用 llmTaskLock 模块

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§Context：设计约束）
