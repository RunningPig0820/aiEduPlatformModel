# 数据来源与数据治理

> summary: 数据来源与数据治理
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-integrate-edukg-02-数据来源与数据治理.md
> 类别：数据关联

## 数据来源：EDUKG TTL

本设计阶段的知识图谱数据来源为 EDUKG 项目提供的 RDF/TTL 数据文件，需从 Google Drive 下载（开放问题：Google Drive 可能需要代理，是否需要提供国内镜像？待决策）。

## EDUKG 可复用组件

EDUKG 提供了以下可复用组件：

| 模块 | 文件 | 功能 | 复用程度 |
|------|------|------|----------|
| 知识图谱处理器 | `kg_handler.py` | TTL 加载、SPARQL 查询 | 高 |
| SPARQL 连接器 | `sparql_query.py` | Jena/Neo4j 连接 | 中（需适配） |
| 实体链接 | `linking.py` | 文本→实体识别 | 高 |
| 本体定义 | `ontology.owl` | 类/属性定义 | 直接使用 |

## 数据可信度与治理约束

- EDUKG TTL 数据文件需要从 Google Drive 下载
- 数据导入依赖 Neo4j n10s 插件对 RDF/TTL 的原生支持（流程见数据导入流水线块）
- 回滚层面：Neo4j 数据通过 TTL 文件可重建，TTL 文件即事实数据源（真理源），数据可随时重建恢复
