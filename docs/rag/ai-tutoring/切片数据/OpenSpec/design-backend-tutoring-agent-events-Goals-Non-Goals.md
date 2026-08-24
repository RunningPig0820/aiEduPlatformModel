# design-backend-tutoring-agent-events

> summary: 明确后端辅导代理事件的目标与非目标范围
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Goals / Non-Goals
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-events

---

## Goals / Non-Goals

**Goals:**
- decide 消费改 SSE：`bodyToFlux(SSE)` 过滤 `meta` 事件取 ActionMeta，空流/error 按 agent 失败处理
- generate 中继 Python 的 `agent` 事件（与 token 一起透传前端）
- 注入 `agent(guardrail)`（护栏通过后、generate 前）与 `agent(memory)`（落库后、流尾）
- 事件格式与模型端协议对齐：`{level:"sub", stage, label, status, detail}`，level 预留 master
- 保持护栏/落库/SSE 业务逻辑不变（只加展示事件，不改决策）

**Non-Goals:**
- **不中继 decide 的 agent 阶段事件**（perceive/analyze/plan/decide）——只中继 decide 的 thinking 推理分片（D7），agent 阶段事件仍不透传，前端 guardrail 前显示"AI 思考中" + 实时推理分片即可。（⚠️ 2026-08-12 **已演进**：decide agent 事件现透传前端，见 `tutoring-agent-workflow-backend` change design D1）
- **decide thinking 不入库**——仅实时透传，历史消息只保留 generate thinking（Redis/COS）；若要 decide thinking 落历史，另立 change
- 不改 ActionMeta 契约内容、不改生成约束（引导式学习不变）
- 不做真实工具调用（知识图谱 agent 为将来）
- 不改前端渲染实现（协议事件透传，渲染由前端配合）
