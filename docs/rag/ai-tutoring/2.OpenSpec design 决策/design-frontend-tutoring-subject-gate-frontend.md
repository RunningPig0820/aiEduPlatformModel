# tutoring-subject-gate-frontend 技术设计

## Context

后端 change `tutoring-subject-gate` 在 `decide` 之前新增学科分类，非数学题（拍题/换题）不建/不续会话、不落库、不耗轮次，返回「仅支持数学」SSE 提示流。对前端，SSE 契约（`meta / token / done`）不变，新增的跳过序列是：

```
event: meta,  data: {"sessionId":null, "status":"ACTIVE", "type":"hint", "roundCount":0}
event: token, data: {"content":"目前仅支持数学答疑，换一道数学题试试吧。"}
event: done,  data: {"sessionId":null, "status":"ACTIVE", "roundCount":0}
```

前端现状（代码验证）：
- `handleMeta`（`useTutoringSession.js:258`）对 `meta.sessionId != null` 才有建会话/持久化/置 active 的动作；`sessionId=null` 走跳过 → 天然不建会话、不持久化、不置 active。
- `meta.type='hint'` 由 `TypeBadge` 渲染为「引导」徽标，`deriveTurnFlow` 对 hint/round=0 无异常。
- `done.status='ACTIVE'` 不触发 ended 分支，`persistSession(null)` 早退。
- 换题非数学：`type=hint`（非 `switch`）→ 前端不渲染「已切换到新题」分隔条；`currentQuestion` 派生自首条 user 消息 → 保持原题。

## Goals / Non-Goals

**Goals:**
- 确认并锁定「拍题非数学」「换题非数学」两条路径的渲染与会话状态不被破坏。
- Agent 工作流在「意图分类」前新增「题型分析」阶段，展示 `meta.topicLabel`，无题型时优雅降级。
- 新增 E2E 回归，覆盖非数学跳过 + 题型分析展示 + 随后数学题正常建会话。
- 对齐后端契约（拍题 `sessionId=null` / 换题 `sessionId=原值`）。

**Non-Goals:**
- 不改前端数据流（学科判定对前端透明，不新增 subject 请求参数）。
- 不做「仅支持数学」差异化展示（弹窗/图标）——后端本期无 meta 标记，且换题非数学与正常 hint 回复在契约上不可区分。
- 不改掌握度/题型分析页。

## Decisions

### 1. 前端数据流不改，靠既有守卫覆盖

`handleMeta` 的 `if (meta.sessionId != null)` 已经天然处理 `sessionId=null`：不持久化、不置 active、不落 localStorage。`handleDone` 对 `status=ACTIVE` 不判 ended、`persistSession(null)` 早退。故 **无必改代码**；本 change 的代码产出为 E2E 测试（锁定行为防回归），若回归发现边界再微加固。

**备选（否决）**：为 `sessionId=null` 加显式分支/提示样式 → 无收益且与「契约透明」冲突。

### 2. 无差异化展示（本期）

后端 api.md 注 5：「若前端希望差异化展示…后续可在 meta 增加标记，本期不新增」。且「换题非数学」的 `sessionId` 为原值、`type=hint`，与正常 hint 回复契约完全一致，前端无法可靠识别。故提示按普通 hint AI 气泡呈现。

### 3. 答疑工作流「题型分析」阶段（意图分类前）

在 `AgentTurnFlow` 的 `TurnStages` 中，`IntentRow`（① 意图分类）之前插入「题型分析」行：渲染 `flow.topicLabel`（题型名），图标 `Tag`/`ScanSearch`，label「题型分析」，文案 `topicLabel` 或「—」占位。`meta` 无 `topicLabel` 时不渲染该行（`TurnStages` 内 `flow.topicLabel` 为空即跳过），保证旧契约降级。

- 数据链路：`meta.topicLabel` → `deriveTurnFlow(meta)` 返回 `topicLabel` → 存进消息 `agentFlow` 快照（随消息持久化，历史回看可复原）→ `TurnStages` 读取 `flow.topicLabel` 渲染。
- **后端依赖**：`meta` 需新增 `topicLabel` 字段（由后端 `tutoring-subject-gate` 的学科门/decide 阶段返回）；后端未上线该字段前，前端「题型分析」行不出现（优雅降级，不阻塞）。
- 备选（否决）：前端并行调 `analyze-question` 获取题型 → 与学科门重复一次 LLM 判定、答疑延迟翻倍，且与「学科判定后端透明」冲突。

### 4. E2E 用 mock SSE 注入非数学序列 + 题型分析序列

沿用 `tutoring-agent-workflow.spec.mjs` 的 `mockTutoringSse`（本地 HTTP 服务分片下发 + `route.fetch` 中继）与 `loginAsStudent`（`/api/unauth/demo-login` 设 Cookie）。按请求路径分发：`POST /api/tutoring/sessions` → 非数学跳过（拍题）；`POST /api/tutoring/sessions/{id}/messages` → 换题非数学（先建正常数学会话再换题）。题型分析用例在正常 math SSE 的 meta 中带 `topicLabel`。

断言重点：
- **拍题非数学**：提示气泡可见、无轮次徽标（「第 1/20 轮」不出现）、无「请求答案」按钮、随后发数学题能建会话（出现「第 1/20 轮」徽标）。
- **换题非数学**：无「已切换到新题」分隔条、「当前题目」文本保持原题、会话仍活跃可再发消息。
- **题型分析**：meta 带 `topicLabel` 时「题型分析」行先于「意图分类」渲染；meta 无 `topicLabel` 时该行不出现。
- 非数学轮次不消耗：roundCount 不变。

## Risks / Trade-offs

- [换题非数学时前端乐观展示的新题图片在刷新后消失（后端不记录）] → 属瞬态展示，接受不处理；后端 transcript 不含该题，刷新即恢复一致。
- [若未来后端加「仅支持数学」meta 标记做差异化展示] → 本期不预埋依赖；届时在 `handleMeta` 按标记渲染提示样式即可，改动局部。
- [分类器误拦/漏拦数学题] → 后端设计已按 math 放行降级；前端无需感知。

## Migration Plan

- 纯前端新增 E2E 测试文件，无部署/数据迁移；后端联调后跑全量 Playwright 回归。
- 回滚：删除测试文件即可，无功能代码改动。

## Open Questions

- 无（前端契约由后端 `tutoring-subject-gate` 定稿，行为已由后端 api.md/spec 明确）。
