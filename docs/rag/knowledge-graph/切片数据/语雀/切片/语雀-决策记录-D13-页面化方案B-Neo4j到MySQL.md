# 页面化方案 B：Neo4j→MySQL 同步，前端读 MySQL

> summary: 图谱页面化怎么做？方案 B——Neo4j 知识点同步到 MySQL，前端 SPA 只读 MySQL，图谱关系（MATCHES_KG 等）不同步、直查 Neo4j。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-决策记录-D13-页面化方案B-Neo4j到MySQL.md
> 类别：操作流程

---

### D13 页面化方案 B：Neo4j→MySQL 同步，前端读 MySQL
> 检索摘要：图谱页面化怎么做？方案 B——Neo4j 知识点同步到 MySQL，前端 SPA 只读 MySQL，图谱关系（MATCHES_KG 等）不同步、直查 Neo4j。

| 属性 | 内容 |
|---|---|
| 背景 | Java 后端无 Neo4j 集成；前端独立 SPA；Neo4j 实时查询重 |
| 演进 | 方案 A（Neo4j 实时查询）被否 → 方案 B |
| 拍板理由 | 前端只读 MySQL 轻量；图谱关系不同步、Neo4j 直查 + Redis TTL 300s + 降级；6,757 节点同步 <10s |
| 系统影响 | 8 张表（4 节点主表 URI 主键 + 3 层级关联 + 1 同步记录）；状态机 active/deleted/merged；手动按需 UPSERT + 大事务 + 对账 |
| 证据 | 证据：语雀-页面化-ui-design.md / design-backend-2026-06-03-knowledge-graph-ui.md Decision 2 |

> 证据：详见 `1.语雀/语雀-决策记录.md`（§D13）
