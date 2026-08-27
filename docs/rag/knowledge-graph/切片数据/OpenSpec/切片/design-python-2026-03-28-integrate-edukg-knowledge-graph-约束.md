# 约束
> summary: Neo4j 已有独立服务器无需部署，EDUKG TTL 需从 Google Drive 下载，实体链接内存词典约占 20MB 内存，后续对接 Milvus 向量库。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-03-28-integrate-edukg-knowledge-graph-约束.md
> 类别：架构设计

> 检索摘要：Neo4j 已有独立服务器无需部署，EDUKG TTL 需从 Google Drive 下载，实体链接内存词典约占 20MB 内存，后续对接 Milvus 向量库。

1. ~~需要部署 Neo4j 图数据库~~ → **已有独立 Neo4j 服务器**
2. EDUKG TTL 数据文件需要从 Google Drive 下载
3. 实体链接使用内存词典，占用 ~20MB 内存
4. 后续需要对接向量数据库（Milvus）

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-03-28-integrate-edukg-knowledge-graph.md`（§约束）
