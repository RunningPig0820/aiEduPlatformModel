## Why

后端新增「学科门」`tutoring-subject-gate`：`decide` 之前用学科无关分类器判定题目学科，非数学题（拍题/换题）**不建/不续会话、不落库、不耗轮次**，直接返回「目前仅支持数学答疑，换一道数学题试试吧。」的 SSE 提示流。对前端，SSE 契约（`meta / token / done`）不变，但新增一种响应场景需要验证渲染与状态不被破坏。

## What Changes

- **数据流不改**（契约透明）：前端照常发题，学科判定在后端完成。
- **验证并锁定「拍题非数学」场景**（`meta.sessionId=null`）：不建会话、不持久化、不置 active、不显示轮次徽标、不出现「请求答案」按钮；提示气泡正常渲染；随后发数学题可正常建新会话。
- **验证并锁定「换题非数学」场景**（活跃会话中发新题）：`meta.type=hint`（非 `switch`）→ 不显示换题分隔条；「当前题目」保持旧题；会话保持活跃可继续。
- **Agent 工作流新增「题型分析」阶段**，置于「① 意图分类」之前：展示后端识别的题型名（`meta.topicLabel`），数据经 `deriveTurnFlow` 注入气泡工作流快照；`meta` 无题型时该阶段不渲染（优雅降级，不阻塞）。
- **新增 E2E 回归**（mock SSE 注入非数学序列 + 题型分析序列），覆盖上述两条路径 + 题型分析展示 + 后续数学题回归。
- 差异化展示（弹窗/图标「仅支持数学」）本期不做——后端未在 meta 增加标记（api.md 注 5），无法可靠区分换题非数学与正常 hint 回复。

## Capabilities

### New Capabilities

- `tutoring-subject-gate`: AI 答疑学科门前端适配——非数学题跳过场景的 SSE 渲染与会话状态不被破坏；答疑 Agent 工作流在「意图分类」前新增「题型分析」阶段；均通过 E2E 锁定。

### Modified Capabilities

- 无（现有 `openspec/specs/` 无 `ai-tutoring` 专属 spec，仅实现细节不升 spec）。

## Impact

- `ai-edu-front/src/hooks/useTutoringSession.js`：确认 `handleMeta`/`handleDone` 对 `sessionId=null` 的既有守卫已覆盖（不持久化、不置 active）；`meta.topicLabel` 经 `deriveTurnFlow` 注入工作流快照。
- `ai-edu-front/src/components/student/ai-qa/AgentTurnFlow.jsx`：新增「题型分析」阶段行（意图分类之前），`meta` 无题型时优雅降级不渲染。
- `ai-edu-front/src/utils/tutoringWorkflow.js`：`deriveTurnFlow` 支持 `topicLabel` 字段。
- `ai-edu-front/tests/tutoring-subject-gate.spec.mjs`：新增 E2E（沿用 `tutoring-agent-workflow.spec.mjs` 的 mock SSE 模式）。
- **后端依赖**：答疑 meta 需携带 `topicLabel`（题型名）——由后端 `tutoring-subject-gate` 的学科门/decide 阶段返回；后端未提供时前端「题型分析」阶段不渲染。
- 对齐后端：`/Users/minzhang/Documents/work/ai/aiEduPlatform/openspec/changes/tutoring-subject-gate`（契约见其 `api.md`「1. 非数学题跳过响应」）。
