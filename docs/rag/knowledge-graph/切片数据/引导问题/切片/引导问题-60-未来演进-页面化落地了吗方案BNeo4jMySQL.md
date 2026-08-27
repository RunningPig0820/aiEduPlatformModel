# 页面化落地了吗？方案 B（Neo4j→MySQL 同步）现在是什么状态？
> summary: 未来演进引导问题回答：方案 B 已拍板、数据层设计完成，但 Java/前端代码不在本仓无法核验真值，design 标注 graph 接口未实现、API 前缀前后端不一致，属"联调收口"状态不能讲成已上线
> 权威度: 1.0（合成问答答案切片，非原始证据）
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/引导问题/引导问题-60-未来演进-页面化落地了吗方案BNeo4jMySQL.md
> 类别：未来演进

**核心结论**：方案 B **已拍板、数据层设计完成，但未到"已上线"**——Java/前端代码不在本仓（无法核验真值），前端 design 标注图谱 graph 接口"后端当前未实现"、API 前缀前后端不一致（/api/kg/** vs /api/auth/kg/**），属"联调收口"状态，只能讲"方案 B 已拍板、数据层设计完成"。

## 分层展开
- **方案 B 内容**：Neo4j 教材知识点同步到 MySQL 8 张表（URI 主键 + 状态机 active/deleted/merged）+ 双数据源 @DS("kg") ai_edu_kg + 前端 React SPA 三栏（左教材树/中 React Flow 关系图/右详情 2 层父级）+ 6 级导航逐级懒加载（6757 节点不一次渲染）；图谱关系（MATCHES_KG/PART_OF/RELATED_TO）不同步，直查 Neo4j + Redis TTL 300s + 降级 `neo4jAvailable:false`（依据：完善文档 08 / 分析-11）。
- **同步策略**：手动按需触发（非 CDC）+ UPSERT 按 URI + 状态机软删除 + 单事务 + 对账（reconciliation_status）；真实踩过的坑：按年级拆子任务 + Redis 分布式锁 + 卡死检测（J-KG11）、下钻慢 SQL 改点击式单层查询（J-KG10）、DISTINCT+ORDER BY 与 ONLY_FULL_GROUP_BY 冲突（J-KG12）（依据：分析-11 / 坑档案 J-KG10/J-KG11/J-KG12）。
- **落地真相（代码不在本仓）**：Java/前端代码不在本仓（aiEduPlatform/、aiEduPlatformFront/ 不存在），分析-11 基于 design 文档撰写并标注"非代码真值"；Python 仓能核验的只有数据管道侧 6,757 节点/20,887 关系导入（依据：分析-11 / 完善文档 08）。
- **联调缺口**：前端 design 原计划 `GET /api/kg/knowledge-points/{uri}/graph`，但标注"后端当前未实现此接口"；API 前缀后端 /api/kg/**、前端 /api/auth/kg/** 不一致，联调易 404（依据：分析-11 / 完善文档 08）。
- **口径提醒**：不能讲成"页面化已上线"——正确表述是"方案 B 已拍板、数据层设计完成、联调收口中"（依据：完善文档 08 / 引导问题.md 6）。

## 追问防御
- **可能追问：页面化算落地了吗？** → 方案 B 已拍板但 Java/前端代码不在本仓、graph 接口未实现、API 前缀不一致，属"联调收口"状态；Python 侧数据管道本仓可核验（依据：引导问题.md 6 / 分析-11）。
- **可能追问：下一步是什么？** → 补 graph 接口、对齐 /api/kg 与 /api/auth/kg 前缀、点亮前端（依据：完善文档 08 / 引导问题.md 9）。
- **可能追问：怎么保证两库一致？** → 手动按需 UPSERT 幂等 + 状态机 + 单事务 + 对账（MySQL vs Neo4j 计数比对 reconciliation_status）（依据：分析-11 / 坑档案 J-KG11）。

> 证据：详见 `4.完善文档/08-演进路线.md` ｜ `3.代码/分析-11-Java同步与前端页面.md` ｜ `5.难点/坑档案.md（J-KG10/J-KG11/J-KG12）`
