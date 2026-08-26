# design-backend-tutoring-agent-events

> summary: 讲答疑编排的接口变更与对接要求
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Context
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-events
> 类别：架构设计

---

## Context

当前 Java 答疑编排（`ai-tutoring` 变更落地）：`decide`（非流式 JSON 返回 ActionMeta）→ Java 护栏 → `generate`（流式 SSE，Java 只透传 token）→ 前端。模型端已完成 `tutoring-agent-protocol` 变更并给出对接契约（`ai-edu-ai-service/docs/ai-tutoring-agent-events.md`）：

- **decide 响应从 JSON 改 SSE 流**：`agent(perceive/analyze/plan/decide)` → `meta(ActionMeta)` → `done`。Java 现在的 `bodyToMono(ActionMeta)` 会坏（**BREAKING**）。
- **generate 流新增 agent 事件**：`meta(action_type) → agent(generate) → token* → done`。
- **memory 归属已定**：由 Java 落库后发，Python 已删占位（不会双发）。
- 已定决策（2026-08 联调）：guardrail 文案"安全把关"、decide 流式后仅首事件前可重试 1 次、流中错误透传 error 不重试、短路/兜底分支同走 SSE 流。

Java 侧三个对接点：① decide SSE 消费（BREAKING）② generate 中继 agent 事件 ③ 注入 guardrail/memory 事件。`TutoringLlmClient.decide` 已按契约改了一半（SSE 解析 + `readActionMeta`），编排层注入尚未完成。
