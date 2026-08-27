# D5 知识点匹配策略
> summary: 匹配策略为精确匹配→LLM 模糊匹配→无匹配 new，输出 matching_report.json 供人工确认，精确匹配成本低先尝试。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/python-2026-04-10-textbook-concept-linking-D5-知识点匹配策略.md
> 类别：数据关联

> 检索摘要：匹配策略为精确匹配→LLM 模糊匹配→无匹配 new，输出 matching_report.json 供人工确认，精确匹配成本低先尝试。

**决策**: 精确匹配 + LLM 模糊匹配，输出报告

```
匹配流程:
1. 精确匹配: label 完全相同 → matched (confidence: 1.0)
2. 模糊匹配: LLM 语义匹配 → fuzzy_match (confidence: 0.8)
3. 无匹配: Concept 不存在 → new (confidence: 0.0)
4. 输出报告: matching_report.json
```

**理由**:
- 精确匹配成本低，先尝试
- LLM 模糊匹配提高匹配率
- 输出报告供人工确认

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-textbook-concept-linking.md`（§D5 知识点匹配策略）
