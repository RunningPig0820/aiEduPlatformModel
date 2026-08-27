# R1 数据导入性能
> summary: EDUKG 数据量 38.6 亿三元组导入耗时，缓解为分学科增量导入、先导入数学物理语文核心学科，独立 Neo4j 服务器性能有保障。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-03-28-integrate-edukg-knowledge-graph-R1-数据导入性能.md
> 类别：开发难点

> 检索摘要：EDUKG 数据量 38.6 亿三元组导入耗时，缓解为分学科增量导入、先导入数学物理语文核心学科，独立 Neo4j 服务器性能有保障。

**风险**: EDUKG 数据量大（38.6亿三元组），导入耗时
**缓解**:
- 分学科增量导入
- 先导入核心学科（数学、物理、语文）
- 已有独立 Neo4j 服务器，性能有保障

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-03-28-integrate-edukg-knowledge-graph.md`（§R1 数据导入性能）
