# design-backend-tutoring-agent-workflow-backend

> summary: 说明后端需补齐的两类契约及当前代码现状问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Context
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-workflow-backend

---

## Context

前端 `show-tutoring-agent-workflow` 需要后端补齐两类契约（见该 change design D2/D3/D5）：
- decide agent 事件透传（"本轮意图"的意图解析 live 数据源）
- meta 新字段（"为什么" hover、知识点分析、掌握度信号）

**现状（已逐条核对代码）**：
- `api/tutoring.py` 已发 `perceive → analyze(processing) → plan(processing) → [thinking*] → agent(decide) → meta`，Java `orchestrate` filter 原只放行 thinking，agent 事件全丢。
- `ActionMeta` 原无 `reason`/`questionKps`；`ACTION_META_MAPPER`（FAIL_ON_UNKNOWN_PROPERTIES=false）容忍并静默丢弃 Python 的 `reason`。
- `SseMetaDTO` 原无 `decideReason`/`questionKps`/`masterySignals`；`reason` 已占位为"护栏拒绝原因"（buildMeta 仅在拒绝时 set）。
- `SseEvalDTO` 无 `masterySignals` → 前端 `meta.eval.masterySignals` 恒 undefined（KpChips 一直无数据）。
- 领域 `MasterySignalItem.kpLabel` 标 `@JsonProperty("kp_label")` → 直接放进 `SseMetaDTO.masterySignals` 会序列化成 snake_case，不符合前端 camelCase 契约。

**本变更落地方式**：后端契约已在工作区实现（filter 透传 + ActionMeta/SseMetaDTO/SseMasterySignalDTO + buildMeta 接线，TutoringAppServiceTest 42/42、TutoringLlmClientTest 3/3 绿）。本 change 作为**后端契约的归属变更**，固化设计决策 + 补齐契约文档（`tutoring-agent-events/api.md`）。
