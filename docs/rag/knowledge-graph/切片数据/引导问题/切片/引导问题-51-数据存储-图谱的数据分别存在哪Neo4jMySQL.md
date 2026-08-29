# 图谱的数据分别存在哪？Neo4j、MySQL、COS 各存什么？

> summary: 数据存储引导问题回答：Neo4j 存 7 类节点/8 类关系权威图谱（URI 主键、只读）；MySQL 存页面化 8 张表（教材结构四主表+层级关联表+同步记录表）；COS 存服务侧向量索引（dashscope 768 维桶，put 后约 10s 异步生效）
> 权威度: 1.0（合成问答答案切片，非原始证据）
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/引导问题/引导问题-51-数据存储-图谱的数据分别存在哪Neo4jMySQL.md
> 类别：数据存储

**核心结论**：Neo4j 存 7 类节点/8 类关系权威图谱（URI 主键、只读）；MySQL 存页面化 8 张表（教材结构四主表 + 层级关联表 + 同步记录表）；COS 存服务侧向量索引（dashscope 768 维桶）。

## 分层展开
- **Neo4j**：7 类节点（Textbook 23/Chapter 148/Section 580/TextbookKP 1740/Concept 1295/Statement 2932/Class 39）+ 8 类关系（CONTAINS/IN_UNIT/MATCHES_KG/HAS_TYPE/RELATED_TO/BELONGS_TO/PART_OF/SUB_CLASS_OF），URI 主键；MATCHES_KG 置信度≥0.5 才连、RELATED_TO 方向固定 Statement→Concept；Python `import/` 脚本写，`api/kg.py` + `api/neo4j.py` 读（依据：完善文档 02 存储拓扑）
- **MySQL（页面化）**：8 张表——t_kg_textbook/chapter/section/knowledge_point 4 主表（URI 主键 + status + merged_to_uri）+ 3 张层级关联表 + 1 张同步记录表（edition/subject/stage/grade 维度 + reconciliation_status）；前端 SPA 读 MySQL，Java 同步（Neo4j→MySQL 手动按需 UPSERT + 状态机，**方案口径，本仓无 Java 代码真值**）（依据：完善文档 02 存储拓扑）
- **COS 向量索引**：服务侧 dashscope 768 维写 COS 桶（`COS_VECTORS_INDEXES` 路由：topic→topic-index / rag-full→rag-full / rag-slice→rag-slice），put 后约 10s 异步生效，**索引维度固定不可改**；匹配侧另用本地 bge 512 文件（kg_vectors.npy），两套维度互相不通用（依据：完善文档 02 存储拓扑 / 分析-09）
- **在线查询坑（）**：在线 service.py 统一 `MATCH (e:Entity {...})`，离线导入用 Textbook/Concept 等具体标签，联调前直接调 `/entities`、`/tree` 可能查不到离线数据（依据：完善文档 02 隐性坑①）

## 追问防御
- **可能追问：谁写谁读？** → Python import 脚本写 Neo4j；Java 同步写 MySQL；vector_store 写 COS；前端只读；图谱关系直查 Neo4j + Redis TTL 300s 缓存降级（依据：引导问题.md 数据存储 / 完善文档 02 存储拓扑）
- **可能追问：Neo4j 查不到数据？** → 在线 `:Entity` 标签 vs 离线具体标签不一致是真实运维坑，联调前必须对齐（Entity 由 Java 动态建 or 查询是期望面）（依据：引导问题.md 最危险问题防御 / 完善文档 02 隐性坑①）

> 证据：详见 `4.完善文档/02-知识图谱数据入库主流程.md`（存储拓扑表）｜ `3.代码/分析-09-向量索引构建与校验.md`
