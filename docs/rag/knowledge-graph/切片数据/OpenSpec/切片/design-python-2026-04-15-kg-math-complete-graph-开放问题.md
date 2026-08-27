# Open Questions 开放问题

> summary: 仍有推断准确率评估、未匹配TextbookKP处理、"通用"标签去留、单元层级方案选择等开放问题待拍板决策。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-开放问题.md
> 类别：未来演进

---

### Open Questions 开放问题

> 检索摘要：仍有推断准确率评估、未匹配TextbookKP处理、"通用"标签去留、单元层级方案选择等开放问题待拍板决策。

1. **Q1**: 教学知识点推断的准确率如何评估？
   - 建议：人工抽查 + 与已知知识点对比

2. **Q2**: 未匹配到知识图谱的 TextbookKP 如何处理？
   - 建议：保留为孤立节点，后续可创建新 Concept

3. **Q3**: "通用"标签数据是否直接删除？
   - 建议：先生成重复检测报告，人工确认后再决定合并或删除

4. **Q4**: 单元/专题层级采用哪种方案？
   - 建议：当前阶段采用方案 B（Chapter.topic 字段），后续迭代可扩展

5. **Q5**: 知识点属性是否需要人工校验？
   - 建议：LLM 推断后生成报告，核心知识点人工复核

6. **Q6**: 多版本教材何时支持？
   - 建议：当前专注人教版，多版本作为 v3.2 版本规划

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§Open Questions 开放问题）
