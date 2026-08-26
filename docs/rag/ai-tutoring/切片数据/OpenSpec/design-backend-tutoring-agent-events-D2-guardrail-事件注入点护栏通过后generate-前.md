# design-backend-tutoring-agent-events

> summary: 确定guardrail事件的注入时机与逻辑
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D2. guardrail 事件注入点：护栏通过后、generate 前
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-events
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-backend-tutoring-agent-events-D2-guardrail-事件注入点护栏通过后generate-前.md
> 类别：架构设计

---

### D2. guardrail 事件注入点：护栏通过后、generate 前

**选择**: `orchestrate` 返回流时 `Flux.concat(agent(guardrail), buildStream(...))`——guardrail 事件在 Java 自建 meta 之前发出。

**时序**: `agent(guardrail) → meta(Java) → agent(generate) → token* → agent(memory) → done`（与模型端文档时序一致）。

**detail**: `guard.isAllowed()` → "放行: {type}"；拒绝 → "拒绝: {type} → 降级 {fallbackType}"（如 "reveal 超限,降级 hint"）。terminate/round-limit 分支（无 generate）本轮不发 guardrail 事件（有各自终止语义）。
