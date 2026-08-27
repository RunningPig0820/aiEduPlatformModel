# 十一、风险与缓解
> summary: 主要风险：v0.1/v3.0数据不匹配、LLM推理不准、年级推断不准、数据量大、relateTo与PREREQUISITE语义混淆，各有缓解措施。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-风险与缓解.md
> 类别：开发难点

> 检索摘要：主要风险：v0.1/v3.0数据不匹配、LLM推理不准、年级推断不准、数据量大、relateTo与PREREQUISITE语义混淆，各有缓解措施。

风险	缓解措施
v0.1 与 v3.0 数据不匹配	通过标签匹配，容忍部分缺失
LLM 推理不准确	置信度阈值过滤（<0.7 丢弃），≥70% 准确率满足 demo
年级推断不准确	提供人工修正接口（正式阶段）
数据量太大	按学科逐个处理，数学先行验证
relateTo 与 PREREQUISITE 语义混淆	严格区分，relateTo → RELATED_TO，LLM → PREREQUISITE

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§十一、风险与缓解）
