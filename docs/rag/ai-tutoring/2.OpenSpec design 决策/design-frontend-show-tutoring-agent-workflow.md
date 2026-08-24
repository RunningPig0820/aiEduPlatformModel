# Design: Show Tutoring Agent Workflow

## Context

AI 答疑已完整上线（decide 判意图 → Java 护栏 → generate 流式正文），2026-08 全关思考模式（`thinking: disabled`），decide 实测 ~1.5s、generate ~1.2s。

**现状（前端可见的 SSE 事件）**：
```
agent(guardrail done) → meta → agent(generate processing) → token* → agent(memory done) → done
```
- Python `api/tutoring.py` **已经**发出 `perceive → analyze → plan → decide` 的 decide 阶段 agent 事件，但 Java `orchestrate` 的 filter 只放行 `thinking`，这些事件**被丢弃**。
- 前端 `AgentStages` 白名单只有 `guardrail/generate/memory`，即使放行也会被忽略。
- `SseMetaDTO` 无 `masterySignals` 字段，前端 `handleDone` 读 `meta.eval.masterySignals` **恒为 undefined**（KpChips 潜在不可用）。
- Python `reason`（决策自由文本）已输出但 Java 不建模，被丢弃。

**要展示的教学流程**（一次答疑 = 一道题的生命周期）：
意图分类 → 澄清 → 分步引导 → 评估 → 知识点确认 → 点亮归档。

## Goals / Non-Goals

**Goals:**
- 新增可折叠「Agent 工作流」面板，**折叠进思考过程区域**（非对话气泡）。
- **每轮 · 本轮意图**（live）：意图解析实时可见（decide agent 事件），决策结果 + "为什么引导/答案"。
- **会话累计 · 题目生命周期**：六阶段逐轮点亮。
- 「为什么」= **确定性推导为主**（type/denied/answerRequestCount/endReason 查表）+ **Python decideReason hover 为辅**。
- **知识点分析（方案 B-lite）**：`question_kps`（可空），完整读题分析功能后续再做。
- 修复 `masterySignals` 契约缺口（meta 补齐），让"知识点确认/评估"有真实数据。

**Non-Goals:**
- 不做完整的"读题知识点分析"独立功能（后续单独 change）。
- 不改动既有答疑行为/决策逻辑（护栏、类型、轮次、收尾均不变）。
- 不做面板的会话持久化（瞬态展示，刷新后随会话状态重建）。
- 不重新设计基础聊天 UI。

## Decisions

### D1. 面板结构：两层（每轮意图 + 会话累计生命周期）

```
┌─ ⚙️ Agent 工作流 ─────────────────────────────┐
│  ◉ 本轮意图 · 实时                             │
│    学生:「还是不懂,给个思路」                    │
│    解析意图 ●→ 求助    → 为什么?               │
│    ✓ 决策:思路大纲 (approach)                  │
│    ↳ 学生明确求助/卡住 → 升级为思路大纲          │
│                                                │
│  ── 题目生命周期 · 累计 ──                      │
│  ① 意图分类     ✓ 第1轮 引导思路 (hint)          │
│  ② 知识点分析   ✓ 二元一次方程组                │
│  ③ 分步引导     ✓✓ 已给 2 步引导                │
│  ④ 澄清         — 未触发                        │
│  ⑤ 评估         ● 学生作答中…                   │
│  ⑥ 点亮归档     待会话结束                       │
└────────────────────────────────────────────────┘
```
- **面板位置**：当前题目卡片下方、聊天线程上方（独立于消息列表）。
- **折叠态**：仅留一行 `⚙️ Agent 工作流 · 意图分类✓ 分步引导✓ ···`；展开看详情。默认展开（面试演示需要）→ 后续可调。
- 六阶段行**累计点亮**：意图分类/知识点分析首轮点亮；分步引导每轮 +1；澄清在 type=concept 轮点亮；评估在收到有效 eval 后点亮；点亮归档在会话结束（ARCHIVED/TERMINATED）点亮。

### D2. 意图分类 live：Java 放行 decide 阶段 agent 事件

- Java `orchestrate` 的 decide filter 从 `only thinking` 改为 `thinking + agent`：
  ```java
  .filter(e -> "thinking".equals(e.event()) || "agent".equals(e.event()))
  ```
- Python decide 流本就是 `perceive → analyze(processing) → plan(processing) → [thinking*] → decide → meta`，Java 透传后前端即可在 decide ~1.5s 内看到意图解析在动。
- **决策结果/为什么**来自 meta（Java 自建），故"本轮意图"在 meta 到达时定型；decide agent 事件是它的"处理中"形态。
- 前端收到顺序（real SSE）：
  ```
  agent(perceive) → agent(analyze) → agent(plan) → agent(decide) → meta → agent(guardrail) → agent(generate) → token* → agent(memory) → done
  ```

### D3. "为什么引导/答案"：确定性推导为主 + decideReason hover 为辅

前端按结构化字段查表（**主文案，常显**）：

| 条件（meta 字段） | 主文案 |
|---|---|
| `denied=reveal` + 第1次要答案 | 护栏:要答案先自己想,先给思路 |
| `type=approach` | 学生求助/卡住,给思路大纲 |
| `type=hint` | 学生正常作答,推一步 |
| `type=concept` | 表述模糊,先澄清 |
| `type=reveal` | 第2次要答案,放行完整解答 |
| `type=switch` | 已切换新题 |
| `type=end` + `endReason` | 按 endReason 映射（COMPLETED→独立解出,点亮归档） |

- **hover 补充**：Python `reason`（自由文本）经 meta 的 `decideReason` 字段透传后作为该行的 title/hover（区别于既有护栏拒绝原因 `meta.reason`，两者语义不同、互不覆盖）。
- 理由：确定性推导 100% 与系统真实决策一致（guardrail 可能覆盖 Python type，只有结构化字段才是最终事实）；decideReason 是模型自由发挥，可能有误/为空，只能作补充。

### D4. 知识点分析（方案 B-lite）：question_kps 可空

- Python decide meta 增加 `question_kps: ["二元一次方程组", ...]`（模型读题时顺手列知识点，**不额外调用**；为空就空）。
- Java `ActionMeta` + `SseMetaDTO` 透传。
- 前端面板②知识点分析：首轮有值显示，为空显示占位"—"。
- **完整"读题知识点分析"独立功能后续做**，届时替换数据源，前端零改动（数据驱动）。

### D5. 数据契约补齐（配套后端改动）

- **Java `ActionMeta`**：新增 `reason`（String，自由文本）、`questionKps`（List<String>）、已有 `masterySignals`。
- **Java `SseMetaDTO`**：新增 `decideReason`（Python 自由文本，区分既有护栏拒绝 `reason`）、`questionKps`、`masterySignals`（数组 `{kpLabel, signal}`，每轮 decide 输出，buildMeta 时带出）。
- **修复潜在缺口**：前端 `handleDone` 不再读 `meta.eval.masterySignals`（undefined），改读 `meta.masterySignals`（meta 事件即带）。
- Python decide agent 事件已是标准协议（`agent_events.py`），零改动。

### D6. 前端实现骨架

- `useTutoringSession`：
  - `handleAgent` 接收全部 stage（去掉白名单过滤，交给面板按需渲染）；新增 `intentStage` 态（derive 自 decide 阶段 agent 事件）。
  - `handleMeta`：记录本轮 intent 结果（type/denied/decideReason/answerRequestCount）+ `questionKps`/`masterySignals` 到面板状态。
  - 面板状态：`workflow`（六阶段累计）+ `currentIntent`（本轮，turn 开始清空）。
- 新建 `AgentWorkflowPanel.jsx`（可折叠、六阶段行、本轮意图区）。
- `ChatThread`/`AiQa`：用面板替换现 `AgentStages` 展示位（chips 逻辑并入面板或废弃）。
- **turn 生命周期**：发送时清空 `currentIntent`、保留累计六阶段；done/error/archive 时定型。

## Risks / Trade-offs

- **decide agent 事件可能快闪**：decide ~1.5s，意图 live 只持续 1.5s 即定型。→ 定型后保留"✓ 决策结果 + 为什么"，观感仍完整；不人为放慢。
- **eval.correct 误判**：`eval.correct=false` 对非 hint/approach 轮是模型默认值（后端 B3 门控）。→ 前端仅在 `meta.type ∈ {hint, approach}` 且无 denied 时显示"回答正确/错误"；其余轮只展示情绪/澄清，避免误导。
- **decideReason 质量**：自由文本可能为空/跑题。→ 主文案用确定性推导，decideReason 仅 hover；空则隐藏 hover。
- **masterySignals 契约变更**：SseMetaDTO 加字段为 additive，旧前端兼容。→ 低风险。
- **面板与 AgentStages 重复**：避免两套展示并存。→ 面板替换 chips 展示位，chips 组件保留但不再接线（或删除）。

## Migration Plan

1. Python：decide meta 加 `question_kps`（可选字段，向后兼容）→ 部署。
2. Java：`orchestrate` filter 放行 agent + `ActionMeta`/`SseMetaDTO` 新字段（additive）→ 部署。
3. 前端：面板组件 + hook 接线 + 契约字段消费 → 构建/联调。
4. 回滚：前端面板不渲染时回退到既有 chips（数据无破坏）；后端字段 additive，回滚仅损失新展示。

## Open Questions

- 面板默认折叠还是展开？（倾向展开，面试演示需要）
- 分步引导在面板中：逐轮列条目，还是计数（"已给 2 步"）？（倾向计数 + 最近一轮详情）
- 评估阶段：逐轮显示 eval，还是仅在学生完成作答（exercise_complete/end）时显示？（倾向逐轮但按 D3 门控，避免误判）

---

# 阶段二：工作流进对话气泡（展示位重构）

> 阶段一（D1-D6）已实现并验证：顶部可折叠 `AgentWorkflowPanel`（每轮意图 + 题目生命周期累计六阶段）。
> 阶段二重构展示位：**六阶段从顶部独立面板移入每个 AI 回答气泡内，每回合重置走一遍**，并新增 SENDING 期 live 走查，让"每次对话都走一遍 agent 管线"直接可见。

## Context（阶段二）

用户确认的展示效果（面试项目主叙事）：
- **位置**：六阶段管线渲染在 **AI 回答气泡内**（类型徽标下、思考面板上、答案正文上方），每回合一张。
- **语义**：**每回合独立走一遍**——每轮对话都从 ①意图分类 开始，逐项点亮；下一回合回到待触发态；⑥ 点亮归档仅在会话结束时点亮（仅末回合）。
- 移除顶部独立面板（不再有"题目生命周期 · 累计"总览）。

```
用户确认预览（气泡内，第 2 回合换题后）:
┌─ AI ● 思路大纲 ───────────┐
│ ① 意图分类   ✓ 已切换新题   │
│ ② 知识点分析 ✓ 二元一次方程组│
│ ③ 分步引导   — 未触发       │
│ ④ 澄清       — 未触发       │
│ ⑤ 评估       ● 学生作答中…  │
│ ⑥ 点亮归档   待会话结束      │
│ ──────────────────        │
│ 正文…                      │
└────────────────────────────┘
```

## Goals / Non-Goals（阶段二）

**Goals:**
- 六阶段进气泡：每个 AI 消息自带本回合管线快照 `agentFlow`，气泡内渲染。
- 每回合重置：①-⑤ 按本回合 meta 派生，⑥ 待会话结束（仅末回合点亮）。
- SENDING live 走查：meta 前（decide 期，实测可长达 17-48s）在聊天线程内显示 live 管线（①"解析意图…"脉动等），**替换打字指示**；meta 到达后气泡接管、live 元素卸载。
- 逐项点亮动画：气泡挂载后 ①→⑤ 步进点亮，强化"agent 走管线"观感。

**Non-Goals:**
- 不做"题目全生命周期累计总览"（用户选择每回合重置；若后续要总览，另加"会话摘要"折叠条）。
- 不改决策逻辑/SSE 契约（复用阶段一 `meta` 字段：type/denied/decideReason/questionKps/eval/status）。
- 不做气泡内管线的持久化新机制（快照随消息落 localStorage，历史回看天然带出）。

## Decisions（阶段二）

### D1-R. 展示位：六阶段进 AI 气泡 + SENDING live 走查

```
┌─ 学生 ──────────────────────────┐
│ 鸡兔同笼,笼子里有 35 个头…        │
└─────────────────────────────────┘
┌─ 🤖 正在走查 agent 管线（SENDING live）───┐
│ ① 意图分类   ● 解析意图…（decide 事件逐片更新 label）│
│ ② 知识点分析 ○ 待首轮读题                      │
│ ③ 分步引导   — 未触发                         │
│ ④ 澄清       — 未触发                         │
│ ⑤ 评估       ● 学生作答中…                    │
│ ⑥ 点亮归档   待会话结束                        │
└────────────────────────────────────┘
              ↓ meta 到达 → 气泡接管（管线结晶，①→⑤ 步进点亮）
┌─ 🤖 思路大纲 ──────────────────┐
│ ① 意图分类   ✓ 思路大纲          │
│ ② 知识点分析 ✓ 鸡兔同笼          │
│ ③ 分步引导   ✓ 已给 1 步引导     │
│ ④ 澄清       — 未触发           │
│ ⑤ 评估       ✓ 回答有误 · 困惑   │
│ ⑥ 点亮归档   待会话结束          │
│ ──────────────────            │
│ 先设鸡有 x 只,兔有 y 只…         │
└─────────────────────────────────┘
```

- **live 元素（SENDING 期，meta 前）**：聊天线程内渲染六阶段管线（与气泡内同布局），**替换打字指示**。驱动：`phase === 'SENDING'` + `intentStage`（decide agent 事件）。① 行 label 随 decide 事件更新：读取题目…/解析意图…/规划引导…/决策完成…；无事件时默认"解析意图…"（避免空窗，兼容换题/降级轮）。⑤ 恒"学生作答中…"，⑥ 恒"待会话结束"。
- **气泡管线（meta 后）**：AI 消息渲染 `agentFlow` 快照，①-⑤ 结晶点亮（带步进动画），⑥ 按会话状态。live 元素卸载。
- **顶部面板移除**：`AiQa` 不再渲染 `AgentWorkflowPanel`；组件文件删除或保留未接线（与阶段一 `AgentStages` 处理方式一致，供回滚）。

### D2-R. 每回合重置：agentFlow 快照派生

纯函数 `deriveTurnFlow(meta)`（新增于 `src/utils/tutoringWorkflow.js`），由结构化 meta 派生**本回合**六阶段，替代阶段一的累计 `updateWorkflow`：

| 阶段 | 本回合点亮条件（meta 字段） | 文案 |
|---|---|---|
| ① 意图分类 | 恒（每回合都有决策） | `第N轮 {typeLabel} ({type})`；switch → "已切换新题" |
| ② 知识点分析 | `questionKps` 非空 | 知识点列表；空 → "—" |
| ③ 分步引导 | `type ∈ {hint, approach, reveal}` | "已给 1 步引导"；否则 "— 未触发" |
| ④ 澄清 | `type === 'concept'` | "已澄清"；否则 "— 未触发" |
| ⑤ 评估 | 门控：`type ∈ {hint, approach}` 且无 `denied` | "回答正确/有误 · 情绪"；非门控 → 情绪或"学生作答中…" |
| ⑥ 点亮归档 | `status ∈ {ARCHIVED, TERMINATED}` | "已归档"；否则 "待会话结束" |

- 与阶段一 D3 的确定性推导一致（护栏覆盖优先、switch 短路、评估门控），作用域从"会话累计"改为"本回合"。
- **逐项点亮动画**：气泡挂载后 ①→⑤ 以 ~150ms 步进点亮（CSS transition，`animate` prop 控制，历史消息可关闭），呈现"agent 走管线"观感；⑥ 仅在会话结束回合点亮。

### D3-R. 数据模型：agentFlow 消息快照

- `startAiMessage(type)`：读 `roundMetaRef.current` → `deriveTurnFlow(meta)` → 存 `msg.agentFlow`。`TERMINATED + reply` 分支的 `replyMsg` 同样派生。
- `toMessage`（服务端 recentMessages）：按可用字段派生——①（typeLabel）、③（`type ∈ GUIDE_TYPES`）、④（`type === 'concept'`）可由 `m.type` 推导；②/⑤/⑥ 缺省占位（历史无完整 meta）。若服务端提供 `question_kps`/`eval`/`status` 一并带入。
- 本地旧消息（无 `agentFlow`）：气泡不渲染管线（优雅降级），不阻塞回看。
- **移除累计 `workflow`/`currentIntent`**：气泡管线由快照驱动，不再需要累计 `workflow` 与 `currentIntent`；live SENDING 仅需 `phase` + `intentStage`。实现：删 `workflow` 态与 `updateWorkflow` 调用、`currentIntent` 态；`clearIntentState` 缩减为只清 `intentStage`。若改动面过大，过渡期可保留字段但不消费（实现时定，设计目标为移除）。

### D4-R. 组件结构

- 新建 `AgentTurnFlow.jsx`（气泡内六阶段管线）：props `{ flow, animate }`；复用阶段一 `StageRow`/`evaluationText`/`EMOTION_LABELS`（从 `AgentWorkflowPanel` 抽出，避免两组件重复）。
- `MessageBubble.jsx`：AI 气泡在思考面板上方渲染 `<AgentTurnFlow flow={message.agentFlow} animate={message.isStreaming} />`。
- `ChatThread.jsx`：SENDING 期渲染 live 管线（同布局，`phase`/`intentStage` 驱动）替换打字指示；新增 props。
- `AiQa.jsx`：移除顶部 `AgentWorkflowPanel` 渲染及相关 props；把 `phase`/`intentStage` 传给 `ChatThread`。

### D5-R. 语义澄清：每回合 vs 累计

- "每次对话走一遍" = 回合视角：每气泡独立走 ①-⑥（⑥ 待会话结束）。回看会话时每轮决策都有对应管线。
- 与阶段一累计面板差异：取消"题目全生命周期总览"；各气泡独立展示回合。优点：每轮决策上下文随气泡走，无顶部长面板；缺点：缺全周期总览（若需要，后续加"会话摘要"折叠条，非本变更）。

## Risks / Trade-offs（阶段二）

- **气泡高度**：每气泡六行管线 + 思考面板 + 正文，长对话气泡偏高。→ 管线行紧凑（小字号、tight 间距）；若过长可对非当前消息默认折叠为摘要行（面试演示默认展开最新消息）。实现时按需。
- **SENDING live 与 decide thinking 并存**：thinking 开启时 SENDING 期同时有思考条 + live 管线。→ 思考条默认收起，管线为主动画；关思考时仅管线，SENDING 不再空窗（比现状打字指示更好）。
- **历史消息无快照**：老消息/服务端消息部分阶段占位。→ 优雅降级 + 按 type 派生，不回退已读内容。
- **移除累计 workflow 的面**：涉及 hook 多处调用点。→ 分步移除，构建/E2E 回归兜底。

## Migration Plan（阶段二）

1. `tutoringWorkflow.js`：新增 `deriveTurnFlow`（纯函数，先独立验证）。
2. hook：`startAiMessage`/`replyMsg`/`toMessage` 派生 `agentFlow`；逐步移除 `workflow`/`currentIntent`。
3. 组件：新建 `AgentTurnFlow` → `MessageBubble` 接线 → `ChatThread` live 管线 → `AiQa` 移除顶部面板。
4. 验证：build + E2E（气泡管线、每回合重置、live 走查、归档末回合、历史降级）+ 回归（换题/降级/关思考）。
5. 回滚：保留 `AgentWorkflowPanel` 未接线，恢复顶部面板即回退阶段二。

## Open Questions（阶段二）

- 气泡内管线密度：六行（如预览）vs 单行紧凑 icon 管线？（倾向六行紧凑，可折叠）
- 非最新消息的管线：恒展开 vs 自动折叠为摘要行？（倾向：面试演示最新消息展开，历史折叠）
- 是否保留"题目生命周期累计总览"入口（如会话摘要条）？（用户选择每回合重置，本变更不做，后续可加）

---

# 阶段三：思考下沉到 Agent 细分工作流（主工作流 + 各 agent 子工作流）

> 阶段二把六阶段做成气泡内每回合管线（AgentTurnFlow），思考仍以独立 ThinkingPanel 挂在管线下方。
> 阶段三把思考**下沉到主工作流的细分工作流**——每个主阶段（agent）内部有自己的步骤条，思考文本是当前活跃子步骤的实时内容。像 DeepSeek 那样"意图识别完成后转入其他子流程"；为将来把意图分类 / 知识点分析拆成独立 agent 预铺：**新增 agent = 注册一条子流程 + 路由其事件，展示层零重构**。

## Context（阶段三）

用户确认的展示方向：
- **现在**：思考过程（独立面板）→ 希望变成 Agent 工作流的**细分工作流**下——主工作流①-⑥里，正在跑的阶段展开自己的子步骤条，思考内容内嵌在活跃子步骤下流式显示。
- **未来**（拆 agent）：意图分类、知识点分析肯定拆成两个 agent。设计要保证"加入其他 agent 时，把该 agent 的流程展示出来"是**注册式**的，不重构展示层。

**数据现状**（已核实，纯前端可行）：
- decide 阶段 agent 事件 `perceive→analyze→plan→decide`（label：读取题目 / 解析意图 / 规划引导 / 决策完成）已透传到前端（`useTutoringSession.handleAgent` 按 stage 去重，`intentStage` 已用）。
- generate 阶段 `agent(generate)→thinking*→token*→agent(memory)` 已流式透传。
- 前端路由**当前靠 phase 推断**（decide 期事件→①，generate 期→③/⑥），单 agent 阶段无歧义。

## Goals / Non-Goals（阶段三）

**Goals:**
- 主工作流①-⑥保持现状（气泡内每回合管线 + live 走查），在其上叠加**细分工作流**展示层。
- 每个被 agent 驱动的主阶段，展开自己的子步骤条；思考文本内嵌为活跃子步骤的实时 detail。
- **注册式扩展**：主阶段 ↔ agent ↔ 子步骤 由注册表描述；新增 agent = 新增注册条目 + 路由其事件，展示层零重构。
- 数据契约尽量复用：子步骤优先由**已透传的 agent 事件**驱动；仅当拆 agent 需要显式归属时，加可选 `agent` 路由字段（additive）。

**Non-Goals:**
- 不改变六阶段主流程、决策逻辑、SSE 契约。
- 不把思考面板做成"子步骤"级别的逐条拆分（模型不吐结构化步骤边界，思考仍是连续流，作为活跃子步骤的 detail 展示，而非强行分段）。
- 不在本阶段真正拆独立 agent（意图分类 / 知识点分析仍走现有 decide 单 agent；子流程注册表预留槽位）。

## Decisions（阶段三）

### D1-S. 展示结构：主工作流 + 细分工作流（两层，嵌套）

```
┌─ 🤖 思路大纲 ──────────────────────────┐
│ ① 意图分类   ✓ 思路大纲                 │  ← 主工作流行（现状）
│   └ 意图识别 ▾ 4/4                      │  ← 细分工作流（嵌套于①下方）
│      ● 读取题目                          │
│        思考: 学生说"还是不懂"…           │  ← 思考 = 子流程唯一 detail,挂首个子步骤
│      ✓ 解析意图                          │  ← 后续步骤直接点亮 ✓(直填写)
│      ✓ 规划引导                          │
│      ✓ 决策:思路大纲                     │
│ ② 知识点分析 ✓ 二元一次方程组            │
│   └ 知识点 ▾ 2/2（读题提取）              │
│      ✓ 读题 → 提取知识点                 │
│ ③ 分步引导   ✓ 已给 1 步引导            │
│   └ 引导 ▾ 2/2                          │
│      ✓ 起草思路                          │
│        思考: 先设鸡有 x 只…              │  ← 引导子流程思考挂首步(起草),token→流式输出
│      ✓ 流式输出                          │
│ ④ 澄清       — 未触发                   │
│ ⑤ 评估       ✓ 回答有误 · 困惑          │
│ ⑥ 点亮归档   待会话结束                 │
└────────────────────────────────────────┘
```

- **主阶段行**保持现状（AgentTurnFlow 六行）。
- 有子步骤的主阶段，行下方**嵌套子步骤条**：头部显示 agent 名 + 进度（`N/M`），子步骤逐项点亮（✓ 完成 / ● 处理中 / ◌ 待触发）。
- **思考 detail**：**子流程级单条**（见 D6-S）——挂载于首个子步骤下方，流式逐字 reveal（复用现有 ThinkingPanel 打字机，缩小为行内 detail）；其余子步骤直填写 ✓，不各挂思考。历史回看时，展开子流程可见该条完整思考（取 `msg.thinking`）。
- 折叠：子流程条默认在**流式 / 处理中展开、定型后可折叠**（面试演示：最新消息展开）。
- 无子步骤的（④澄清，或未触发阶段）不渲染子流程，保持单行。

### D2-S. 子步骤数据来源：优先复用 agent 事件，事件驱动

子步骤的状态（label/✓/●）由**已透传的 agent 事件**驱动，不新增后端事件：

| 主阶段 | agent | 子步骤（事件驱动） | 数据来源 |
|---|---|---|---|
| ① 意图分类 | 意图识别 | 读取题目 → 解析意图 → 规划引导 → 决策完成 | decide 的 perceive/analyze/plan/decide 事件（已透传） |
| ② 知识点分析 | 知识点（预留） | 读题 → 提取知识点 → 确认 | 现在：meta.questionKps（无独立事件，"读题"借 ① 的 perceive 标记完成）；未来：独立 agent 事件 |
| ③ 分步引导 | 引导 | 起草思路 → 流式输出 | generate 的 agent(generate) + thinking + token |
| ⑥ 点亮归档 | 记忆 | 归档总结 | generate 尾段 agent(memory) |

- 路由归属：**当前靠 phase 推断**（decide 期→①，generate 期→③/⑥），单 agent 无歧义，纯前端即可做。
- ② 现在无独立事件：子流程显示"读题 → 提取知识点"，"读题"借 ① 的 perceive 事件标记完成，"提取知识点"借 meta.questionKps 定型。未来拆独立 agent 后由该 agent 事件驱动，前端零结构改动。

### D6-S. 思考 = 子流程级单条 detail（一次性展示，非逐步骤）

**实测事实**：一个 agent 的多个子步骤由**一条连续思考流**产生。decide 时序为 `perceive→analyze→plan 事件瞬间到 → thinking*（32 片连续流）→ agent(decide)`——模型不吐分步推理，`reasoning_content` 是一整条，硬拆成逐步骤是假的。

**展示规则**：
- 思考作为该子流程的**唯一 detail**，挂载于**首个子步骤**下（意图识别→读取题目；引导→起草思路），流式逐字 reveal。
- 其余子步骤（解析意图/规划引导/决策完成）到达事件时**直接点亮 ✓（直填写）**，不再各挂思考文本。
- 叙事一致性：前三个事件瞬间 ✓（系统标签），思考流是实际推理主体，decide 事件到达收尾 ✓——"读题即推理，逐步收敛到决策"。
- 例外：③ 引导子流程 thinking↔起草思路、token↔流式输出，天然 1:1，不受本条影响（仍是单条 detail，只是恰好对应首个子步骤）。
- 历史回看：展开子流程见该条完整思考（取 `msg.thinking`），非逐步骤分段。

### D3-S. 注册表：主阶段 ↔ agent ↔ 子步骤（可扩展）

新建 `src/utils/agentSubflows.js`（独立于 `tutoringWorkflow.js` 或合入）维护注册表：

```js
// 主阶段 → agent 细分工作流定义（未来新增 agent = 新增条目，前端结构零改动）
export const AGENT_SUBFLOWS = {
  intent:   { label: '意图识别', steps: [{ev:'perceive',label:'读取题目'},{ev:'analyze',label:'解析意图'},{ev:'plan',label:'规划引导'},{ev:'decide',label:'决策完成'}] },
  guide:    { label: '引导',     steps: [{ev:'generate',label:'起草思路'},{ev:'stream',label:'流式输出'}] },
  archive:  { label: '记忆',     steps: [{ev:'memory',label:'归档总结'}] },
  // 未来（拆独立 agent 时启用）：
  knowledge:{ label: '知识点',   steps: [{ev:'tool',label:'检索知识图谱'},{ev:'analyze',label:'提取知识点'},{ev:'confirm',label:'确认'}] },
  evaluate: { label: '评估',     steps: [{ev:'analyze',label:'读取作答'},{ev:'decide',label:'判定'}] },
}
```

- 每条目：主阶段 key + agent 名 + 子步骤序列（每步绑定一个触发事件 key）。
- 事件 → 子步骤状态推进：`{agent?, event} → (主阶段, 子步骤 index, status)`；缺省（单 agent 期）按 phase + stage 推断归属主阶段。
- 子步骤 detail（思考）：decide 期 → ①，generate 期 → ③，由 handleThinking 同时写 `thinking`（消息字段，落库）与"活跃子步骤 detail"（展示）。

### D4-S. 协议：可选 `agent` 路由字段（additive，拆 agent 时必加）

- Python `agent_events.agent_event(...)` 增加可选 `agent` 字段（子 agent 标识，如 `intent/knowledge/guide/archive`）；现在缺省（前端按 phase 推断）。
- Java 透传该字段（additive，事件体原样转发）。
- 前端：事件带 `agent` → 按 agent 路由到对应子流程；不带 → 按 phase+stage 推断（现状）。
- **作用**：拆独立 agent 时，两个 agent 都发 analyze/decide，靠 `agent` 字段区分归属，前端注册表零结构改动。

> **时机决策**：D4 现在可不做（纯前端能完成子流程展示，行为不变）。拆 agent 前必须做。设计已定字段语义，届时只填值。

### D5-S. 消息快照与历史回看

- `agentFlow` 扩展：`{ stages:[{ id,status,label, subSteps:[{ev,label,status}] }] }`。子步骤状态随消息快照持久化，历史回看按快照复原。
- 思考 detail 历史：复用 `msg.thinking`（现有字段，已随消息落库）。展开子流程时，活跃子步骤下显示 `msg.thinking` 全文（与 ThinkingPanel 历史行为一致）。
- 服务端 recentMessages 无完整子步骤 → 按 type/phase 派生默认子流程（注册表模板 + 状态推断），同阶段二降级策略。

## Risks / Trade-offs（阶段三）

- **气泡高度**：嵌套子流程让气泡更宽/高。→ 子步骤行紧凑（小字号、tight 间距）；定型后默认折叠为 `N/M` 摘要行；面试演示最新消息展开。
- **思考 detail 与 ThinkingPanel 并存/替代**：思考从独立面板移入子流程 detail。→ 阶段三目标就是**合并**：移除独立 ThinkingPanel（或保留为"展开子流程后的完整思考"入口），避免两处展示同一内容。
- **路由推断边界**：现在靠 phase 推断，拆 agent 后必须靠 `agent` 字段。→ D4 已定字段语义，拆 agent 是触发条件。
- **② 无事件驱动**：知识点子流程现在靠数据+借事件，步骤语义弱。→ 接受（占位演示），拆独立 agent 后转正。

## Migration Plan（阶段三）

1. 纯前端骨架：`agentSubflows.js` 注册表 + `deriveTurnFlow` 扩展出 `subSteps`（先独立验证）。
2. hook：`handleAgent`/`handleThinking` 同时推进子步骤状态与 detail；`agentFlow` 快照含子步骤。
3. 组件：`AgentTurnFlow` 渲染嵌套子流程条；`ChatThread` live 走查同步嵌套；移除/收敛 ThinkingPanel。
4. 验证：build + E2E（子流程逐项点亮、思考 detail 内嵌、历史复原、折叠）+ 回归（关思考/换题/降级/无子流程阶段）。
5. （拆 agent 时）D4：`agent` 字段 + 新注册条目。

## Open Questions（阶段三）— 已全部定案 ✅

- ~~思考 detail 位置~~ **已定案（D6-S）**：子流程级单条 detail，挂载于**首个子步骤**下（"第一个思考 + 后续直填写"）；活跃子步骤/横跨块下方方案均弃。
- ~~② 知识点子流程时机~~ **已定案**：现在就展示"读题→提取"占位子流程（读题借 ① 的 perceive 事件点亮、提取借 meta.questionKps 定型），保持六阶段子流程叙事一致；拆独立 agent 后数据源无缝切换，前端零结构改动。
- ~~定型后折叠策略~~ **已定案**：最新消息展开、历史折叠（与阶段二一致，面试演示最新消息为焦点）。
