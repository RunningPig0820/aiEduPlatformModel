# 选型3 数据导入方式：CSV 批量 vs n10s TTL 导入
> summary: 图谱数据导入 Neo4j 用哪种？CSV 批量导入（neo4j-admin/LOAD CSV）是 TTL 导入（n10s）性能 10 倍以上。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-方案选型对比-选型3-为什么选CSV批量不用n10s.md
> 类别：架构设计

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| CSV 批量（LOAD CSV/UNWIND/MERGE） | 快 10x+、MERGE 幂等、断点可控 | 需先生成 CSV | ✅ 采用 |
| n10s rdf.import（TTL 直导） | 原生 RDF | 性能差、难控制 | ❌ 早期试后放弃 |
| 证据 | 证据：语雀-知识图谱数据清洗方案.md / design-integrate-edukg D2 |  |  |

> 证据：详见 `1.语雀/语雀-方案选型对比.md`（选型3）
