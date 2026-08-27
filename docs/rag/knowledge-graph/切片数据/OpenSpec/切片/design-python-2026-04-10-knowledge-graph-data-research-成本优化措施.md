# 14.2 成本优化措施
> summary: 成本优化六招：优先免费模型 GLM-4-flash 主力、付费模型仅投票验证、结果缓存防重复、批量处理、成本监控告警、免费模型多轮验证。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-成本优化措施.md
> 类别：业务视角

> 检索摘要：成本优化六招：优先免费模型 GLM-4-flash 主力、付费模型仅投票验证、结果缓存防重复、批量处理、成本监控告警、免费模型多轮验证。

1. 优先免费模型：GLM-4-flash 作为主力，免费
2. 付费模型仅在必要时：验证高价值关系（投票阶段）
3. 结果缓存：所有调用持久化，避免重复
4. 批量处理：减少调用次数
5. 成本监控：实时累积，超限告警
6. GLM 多轮验证：免费模型可多轮验证，提升准确率而不增加成本

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§14.2 成本优化措施）
