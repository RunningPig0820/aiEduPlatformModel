# design-backend-tutoring-agent-events

> summary: 说明decide消费SSE的实现方案及演进情况
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D1. decide 消费：`bodyToFlux(SSE)` + 过滤 meta 事件（blockLast 同步取）
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-events
> 类别：架构设计

---

### D1. decide 消费：`bodyToFlux(SSE)` + 过滤 meta 事件（blockLast 同步取）

**选择**: 按模型端契约 §二，`decide()` 内部 `bodyToFlux(ServerSentEvent)` → `.filter("meta")` → `map(readActionMeta)` → `.next()` → `.block(decideTimeout)`。无 meta 事件（Python 发 `event: error` 或空流）→ 抛 `TutoringAgentException`（50005，会话保持）。

**原因**: 契约明确、改动最小（端口返回类型不变 `ActionMeta decide(ctx)`，编排层不用动）。decide 的 agent 阶段事件被丢弃（见 Non-Goals）。

**演进（2026-08-13，见 D7）**: D1 为上一阶段落地形态。因 decide 长等待（17~48s）是黑盒，演进为响应式中继 decide thinking（见 D7），decide 消费从"同步 blockLast 取 meta"改为"响应式中继 thinking + 提取 meta"。
