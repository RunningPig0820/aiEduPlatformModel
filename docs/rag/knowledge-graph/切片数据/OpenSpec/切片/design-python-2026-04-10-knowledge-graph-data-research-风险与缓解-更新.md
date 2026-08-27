# 十五、风险与缓解（更新）
> summary: 更新风险清单：断点续传/缓存防重复计费、版本目录+MERGE防误删、SQLite事务、成本监控、进程锁、Graceful Shutdown 等。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-风险与缓解-更新.md
> 类别：开发难点

> 检索摘要：更新风险清单：断点续传/缓存防重复计费、版本目录+MERGE防误删、SQLite事务、成本监控、进程锁、Graceful Shutdown 等。

风险	缓解措施
任务中断导致重复工作	断点续传 + SQLite 状态记录
付费模型重复调用	SHA256 缓存 + 状态表
脚本误删已有数据	版本目录隔离 + Neo4j MERGE
版本混乱	独立目录 + manifest 元数据
处理状态丢失	SQLite 事务保护
成本超预算	实时监控 + 告警 + 限制
误启动多进程	进程锁机制
用户手动中断无保存	Graceful Shutdown
知识点类型缺失	CSV 必须导出 type 列
relateTo 语义混淆	严格区分 RELATED_TO vs PREREQUISITE

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§十五、风险与缓解（更新））
