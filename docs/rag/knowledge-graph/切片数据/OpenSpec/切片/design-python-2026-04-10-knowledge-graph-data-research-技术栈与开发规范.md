# 十、技术栈与开发规范
> summary: 技术栈选型：Python 3.10+、rdflib 解析 TTL、neo4j-driver 4.4.x、复用 LLM Gateway，脚本独立依赖不污染主服务。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-技术栈与开发规范.md
> 类别：架构设计

> 检索摘要：技术栈选型：Python 3.10+、rdflib 解析 TTL、neo4j-driver 4.4.x、复用 LLM Gateway，脚本独立依赖不污染主服务。

#### 10.1 技术栈
> 检索摘要：技术栈：Python 3.10+、rdflib 解析 TTL、neo4j-driver 4.4.x 与 Neo4j 版本严格匹配、LLM 复用现有 Gateway。

技术项	选择	说明
Python 版本	3.10+	与主服务一致，避免环境冲突
TTL 解析库	rdflib	Python 生态最成熟的 RDF 解析库
Neo4j 驱动	neo4j-driver 4.4.x	与 Neo4j 版本严格匹配
LLM 调用	复用 Gateway	使用现有 core/gateway/factory.py

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§十、技术栈与开发规范）
