# Risk 1: 文件损坏
> summary: 状态文件损坏会导致任务无法恢复，通过更新前备份与原子写入缓解。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-08-kg-infrastructure-init-risk1-文件损坏.md
> 类别：开发难点

> 检索摘要：状态文件损坏会导致任务无法恢复，通过更新前备份与原子写入缓解。

**风险**: 状态文件损坏导致无法恢复
**缓解**: 每次更新前备份，使用原子写入

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-08-kg-infrastructure-init.md`（§Risk 1: 文件损坏）
