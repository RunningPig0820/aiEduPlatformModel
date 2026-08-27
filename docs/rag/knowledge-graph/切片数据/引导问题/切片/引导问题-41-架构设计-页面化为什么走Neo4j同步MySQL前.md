# 页面化为什么走"Neo4j 同步 MySQL、前端读 MySQL"，而不是前端直查图库？

> summary: 架构设计引导问题回答：方案A(Neo4j实时查询)被否——Java无Neo4j集成、前端独立SPA、实时查询重；改为方案B(Neo4j→MySQL同步、前端只读MySQL)，图谱关系仍直查Neo4j
> 权威度: 1.0（合成问答答案切片，非原始证据）
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/引导问题/引导问题-41-架构设计-页面化为什么走Neo4j同步MySQL前.md
> 类别：架构设计

**核心结论**：早期方案 A（Neo4j 实时查询、Java 直连图库）被否——Java 没有 Neo4j 集成、前端是独立 SPA、实时查询重；演进为方案 B：Neo4j→MySQL 同步、前端只读 MySQL，图谱关系仍直查 Neo4j。

## 分层展开
- **方案演进**：早期方案 A（Neo4j 实时查询，Java 直连图库）被否；已演进为方案 B：Neo4j→MySQL 同步，前端只读 MySQL，图谱关系仍直查 Neo4j（决策 D13）。（依据：完善文档 03 / 分析-11）
- **否决原因**：Java 没有 Neo4j 集成、前端是独立 SPA、Neo4j 实时查询重——消费侧多元但单点扛不住，前端直查图库不成立。（依据：完善文档 03）
- **方案 B 设计**：8 张表（4 节点主表 URI 主键 + 3 层级关联含 order_index + 1 同步记录）、@DS("kg") 双数据源（业务 Mapper 默认 user 库、图谱 Mapper 路由 ai_edu_kg）、状态机 active/deleted/merged、单大事务 UPSERT + 对账校验；图谱关系（MATCHES_KG/PART_OF/RELATED_TO）**不同步**、直查 Neo4j + Redis TTL 300s + `neo4jAvailable:false` 降级。（依据：完善文档 03 / 分析-11）
- **避免污染权威图**：MySQL 只存节点属性 + 层级关系，图谱关系直查 Neo4j 而非同步——避免无限业务事实污染权威图谱，配合决策 D17 权威图谱零写入。（依据：分析-11）
- **⚠️ 落地边界**：方案 B 已拍板、design 三份一致，但 Java/前端代码不在本仓（aiEduPlatform/aiEduPlatformFront 不存在），分析-11 基于 design 标注"非代码真值"；graph 接口未实现、API 前缀前后端不一致（/api/kg/** vs /api/auth/kg/**）是 design 内自相矛盾。（依据：完善文档 03 / 分析-11）

## 追问防御
- **可能追问：同步怎么保证两边数据一致？** → 手动按需（非 CDC）按 URI UPSERT 幂等可重跑 + 状态机 active/deleted/merged 软删可回溯 + 单大事务内重建关联表 + 同步后 MySQL vs Neo4j 计数对账。（依据：完善文档 03 / 分析-11）
- **可能追问：图谱关系查不到怎么办？** → Redis key `kg:neo4j:{uri}:{query_type}` TTL 300s 缓存；Neo4j 不可用返回空关联 + `neo4jAvailable:false`，前端隐藏图谱模块，导航不依赖图谱可用性。（依据：完善文档 03 / 分析-11）
- **可能追问：页面化算落地了吗？** → 方案 B 已拍板但 Java/前端代码不在本仓、graph 接口未实现、API 前缀不一致，属"联调收口"状态；Python 侧数据管道本仓可核验。（依据：完善文档 03 / 分析-11）

> 证据：详见 `4.完善文档/03-架构与三端分工.md` ｜ `3.代码/分析-11-Java同步与前端页面.md`
