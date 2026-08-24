## Why

模型端（`ai-edu-ai-service`）已完成 `tutoring-agent-protocol` 变更：**decide 响应从 JSON 改为 SSE 流**（agent 阶段事件 → meta(ActionMeta) → done），并定义了标准 agent 事件协议。Java 当前的 `bodyToMono(ActionMeta)` 消费方式已失效（**BREAKING**），必须跟进。同时，agent 事件协议让前端能展示答疑思考流程（读取题目→解析意图→规划引导→决策→安全把关→生成→记忆），把 40s+ 的等待黑盒变成可见进展；Java 的把关（护栏）与记忆（掌握度落库）是真实动作，作为事件展示符合"Python=决策智能、Java=把关+流程控制"的分工。

## What Changes

- **BREAKING**: `TutoringLlmClient.decide` 从"读响应 JSON（`bodyToMono(ActionMeta)`）"改"解析 SSE 流，过滤 `meta` 事件取 data 作为 ActionMeta"。重试语义保留（仅"未收到任何事件"的连接失败可重试 1 次）；空流/`event: error`（无 meta）→ 视为 agent 调用失败（50005，会话保持）。
- **中继 generate 的 agent 事件**：`TutoringAppService.buildStream` 目前只透传 `token` 事件，需同时透传 Python generate 流的 `agent` 事件（如 `generate` 阶段），供前端渲染。
- **注入 guardrail 事件**：护栏审批通过后、调 generate 前，由 Java 发 `event: agent {stage:"guardrail", label:"安全把关", status:"done"}`（detail 带拒绝摘要或放行类型）。
- **注入 memory 事件**：掌握度落库（`TutoringKpResolver` 解析 label→URI + `t_student_kp_mastery` 更新 + `TutoringTranscriptArchiver` 归档）后，由 Java 发 `event: agent {stage:"memory", label:"记忆更新", status:"done"}`。**memory 由 Java 发，Python 已删占位，不会双发**。
- **前端契约变化**：SSE 流新增 `event: agent`（`{level, stage, label, status, detail}`），前端按阶段渲染进度条/标签。

## Capabilities

### New Capabilities
- `tutoring-agent-events`: 答疑 agent 事件协议接入——decide SSE 流式消费、generate agent 事件中继、Java guardrail/memory 事件注入、事件格式 `{level,stage,label,status,detail}` 与标准阶段表

### Modified Capabilities
<!-- 无既有 spec 涉及本变更（ai-tutoring 未提升为独立 spec），本次为新增能力 -->

## Impact

- **`TutoringLlmPort` / `TutoringLlmClient`**：decide 消费方式（SSE 解析 meta 事件），新增 `readActionMeta` + ObjectMapper
- **`TutoringAppService`**：编排层注入 `agent(guardrail)`（护栏后、generate 前）与 `agent(memory)`（落库后、流尾）；`buildStream` 中继 agent 事件
- **前端**：新增 `event: agent` 渲染（阶段进度）；SSE 事件序列从 `meta→token→done` 变为 `agent(guardrail)→meta→agent(generate)→token*→agent(memory)→done`
- **测试**：`TutoringLlmClient`（decide SSE 解析）、`TutoringAppService`（guardrail/memory 事件、agent 中继）、`TutoringController`（SSE 事件序列）
- **契约**：decide 响应格式 breaking（与模型端 `tutoring-agent-protocol` 已对齐，参考 `ai-edu-ai-service/docs/ai-tutoring-agent-events.md`）
