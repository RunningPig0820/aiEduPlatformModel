# 异常处理和输出完整性

> summary: 异常处理：LLM调用失败时continue不中断整个知识点，输出所有教材知识点（含未匹配）并增加matched字段。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D4-5-异常处理和输出完整性.md
> 类别：操作流程

---

### D4.5：异常处理和输出完整性

> 检索摘要：异常处理：LLM调用失败时continue不中断整个知识点，输出所有教材知识点（含未匹配）并增加matched字段。

- LLM 调用失败时 `continue`，不中断整个知识点
- 输出所有教材知识点（含未匹配），增加 `matched` 字段

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D4.5：异常处理和输出完整性）
