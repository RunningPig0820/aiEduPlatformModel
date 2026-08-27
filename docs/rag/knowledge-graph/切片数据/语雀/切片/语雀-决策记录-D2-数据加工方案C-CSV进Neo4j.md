# 数据加工方案 C：CSV→Neo4j

> summary: 图谱数据怎么进 Neo4j？选方案 C——关系处理在 Python 内存/CSV 完成，批量导入 Neo4j，权威基准冻结、教研可维护 CSV。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-决策记录-D2-数据加工方案C-CSV进Neo4j.md
> 类别：架构设计

---

### D2 数据加工方案 C：CSV→Neo4j（vs 直接 TTL 导入）
> 检索摘要：图谱数据怎么进 Neo4j？选方案 C——关系处理在 Python 内存/CSV 完成，批量导入 Neo4j，权威基准冻结、教研可维护 CSV。

| 属性 | 内容 |
|---|---|
| 背景 | 原始基准 TTL 冻结只读，业务 CSV 独立维护；TTL 直接导入性能差 |
| 演进 | 方案 A（TTL 直导）/ 方案 B 被排除 → 方案 C 唯一最优 |
| 拍板理由 | 权威基准冻结；教材章节差异用 CSV 管理；`neo4j-admin import` 性能远超 TTL 导入（10x+）；教研人员可维护 CSV；计算与存储分离 |
| 系统影响 | 离线构建 → CSV → MERGE 幂等批量导入；Neo4j 只是最后仓库 |
| 证据 | 证据：语雀-知识图谱数据清洗方案.md |

> 证据：详见 `1.语雀/语雀-决策记录.md`（§D2）
