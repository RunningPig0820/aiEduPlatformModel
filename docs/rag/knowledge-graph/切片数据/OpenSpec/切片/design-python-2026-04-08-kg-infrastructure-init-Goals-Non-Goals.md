# Goals / Non-Goals
> summary: 目标为实现 TaskState 任务状态、LLMCache 缓存与断点续传及进度恢复；不做分布式调度、Web UI 与复杂成本监控。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-08-kg-infrastructure-init-Goals-Non-Goals.md
> 类别：架构设计

> 检索摘要：目标为实现 TaskState 任务状态、LLMCache 缓存与断点续传及进度恢复；不做分布式调度、Web UI 与复杂成本监控。

**Goals:**
- 实现任务状态管理（TaskState）
- 实现 LLM 缓存机制（LLMCache）
- 实现断点续传支持
- 实现进度显示和恢复

**Non-Goals:**
- 不实现分布式任务调度
- 不实现 Web UI
- 不实现复杂的成本监控（免费模型不需要）

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-08-kg-infrastructure-init.md`（§Goals / Non-Goals）
