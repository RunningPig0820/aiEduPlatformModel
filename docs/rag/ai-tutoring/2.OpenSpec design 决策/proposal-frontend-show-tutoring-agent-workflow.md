# Show Tutoring Agent Workflow

## Why

AI 答疑功能已完整，但这是面试项目——产品本质是"意图分类 → 澄清 → 分步引导 → 评估 → 知识点确认 → 点亮归档"的 agent 编排过程，目前这个过程对用户完全不可见：前端只展示 3 个基础设施 chips（安全把关/生成中/记忆更新），且 2026-08 关思考后"思考过程"面板恒为空。需要把 agent 的**决策与教学流程**折叠进"思考过程"面板展示出来——既是产品价值（学生看懂"为什么给引导/答案"），更是面试项目的主叙事。

## What Changes

- 新增可折叠「**Agent 工作流**」面板（折叠进思考过程区域，非对话气泡），两层结构：
  - **每轮 · 本轮意图**（live）：解析学生提问意图 → 决策类型 → "为什么引导/答案"。意图解析过程实时可见（decide 阶段）。
  - **会话累计 · 题目生命周期**：意图分类 / 知识点分析 / 分步引导 / 澄清 / 评估 / 点亮归档，六阶段随会话生长、逐步点亮。
- 「为什么引导/答案」**确定性推导为主**（前端依据 type/denied/answerRequestCount/endReason 查表）+ **Python decideReason hover 为辅**。
- **知识点分析（方案 B-lite）**：Python decide 输出 `question_kps`（可空），首轮读题即分析涉及知识点；独立"读题知识点分析"功能后续再做，前端该槽位数据驱动（为空显示占位）。
- **后端契约补齐**（配套改动，契约依赖）：
  - Java `orchestrate` 放行 decide 阶段 agent 事件（perceive/analyze/plan/decide），使意图分类 live。
  - `ActionMeta` 新增 `reason`/`question_kps`；`SseMetaDTO` 新增 `decideReason`（Python 自由文本，区别于既有护栏拒绝 `reason`）、`questionKps`、`masterySignals`（修复现有 `meta.eval.masterySignals` 恒空的潜在缺口）。
- Python decide meta 增加 `question_kps`（轻量，可空）。

## Capabilities

### New Capabilities

- `tutoring-agent-workflow`: Agent 工作流面板展示——本轮意图实时解析（decide agent 事件 + 确定性"为什么"推导）+ 题目六阶段生命周期（意图分类/知识点分析/分步引导/澄清/评估/点亮归档）折叠进思考过程。

### Modified Capabilities

<!-- 无既有 spec 需求变更：本变更是新增展示层，不改动既有答疑行为。 -->

## Impact

- **前端（主）**：`useTutoringSession`（decide agent 事件接收、meta 新字段 decideReason/questionKps/masterySignals、面板状态）、新建 `AgentWorkflowPanel` 组件、`ChatThread`/`AiQa` 接线。
- **后端（aiEduPlatform，配套）**：`TutoringAppService.orchestrate` filter 放行 agent 事件；`ActionMeta` 建模 reason/questionKps；`SseMetaDTO` 加 decideReason/questionKps/masterySignals。
- **Python（aiEduPlatformModel，配套）**：`decider.py` decide meta 输出 `question_kps`（可空）。
- **数据契约**：SSE `meta` 事件新增字段；decide 阶段 agent 事件由"不透传"改为"透传"。

---

# 阶段二：工作流进对话气泡（展示位重构）

## Why

阶段一已把 agent 流程做成顶部可折叠面板（每轮意图 + 题目生命周期累计六阶段）。用户进一步要求：agent 工作流要**放进对话本身**——每次对话都走一遍 ①意图分类 → ②知识点分析 → ③分步引导 → ④澄清 → ⑤评估 → ⑥点亮归档 这条管线，让"agent 在工作"成为对话流的一部分，而非顶部一块独立面板。

## What Changes

- **展示位重构**：六阶段从顶部独立面板**移入每个 AI 回答气泡内**（类型徽标下、思考面板上、正文上方），每回合一张。
- **每回合重置**：每轮对话从 ①意图分类 开始逐项点亮；下一回合回到待触发态；⑥ 点亮归档仅在会话结束回合点亮。每消息携带本回合 `agentFlow` 快照（由 meta 确定性派生），随消息持久化。
- **SENDING live 走查**：meta 前（decide 期）在聊天线程内渲染 live 六阶段管线（①"解析意图…"脉动等），替换打字指示——关思考模式下 SENDING 不再空窗。
- **移除顶部面板**：`AiQa` 不再渲染 `AgentWorkflowPanel`；累计 `workflow`/`currentIntent` 态随之下沉到消息快照。
- **派生工具**：`tutoringWorkflow.js` 新增 `deriveTurnFlow(meta)`（每回合快照，替代累计 `updateWorkflow`）。
- **新增组件**：`AgentTurnFlow.jsx`（气泡内六阶段管线，复用阶段一 StageRow/评估文案逻辑）。

## Impact（阶段二）

- **前端（纯前端重构，无后端/Python 改动）**：`useTutoringSession`（`startAiMessage`/`replyMsg`/`toMessage` 派生 `agentFlow`；移除 `workflow`/`currentIntent`）、新建 `AgentTurnFlow`、`MessageBubble`/`ChatThread`/`AiQa` 接线。
- **数据契约**：无新增字段——完全复用阶段一 `meta` 字段（type/denied/decideReason/questionKps/eval/status）。

---

# 阶段三：思考下沉到 Agent 细分工作流

## Why

阶段二把六阶段做成气泡内管线，但思考仍是独立面板（ThinkingPanel）挂在管线下方，与主工作流割裂。用户要求：思考要变成 Agent 工作流的**细分工作流**——正在跑的主阶段（agent）展开自己的内部子步骤条，思考文本内嵌在活跃子步骤下流式显示，像 DeepSeek 那样"意图识别完成后转入其他子流程"。设计成注册式，为后续把意图分类 / 知识点分析拆成独立 agent 预铺——**新增 agent = 注册一条子流程 + 路由其事件，展示层零重构**。

## What Changes（阶段三）

- **两层工作流展示**：主工作流①-⑥保持现状（气泡内每回合管线 + live 走查），有子步骤的主阶段（①意图识别 / ②知识点 / ③引导 / ⑥记忆）行下嵌套**细分工作流**步骤条（agent 名 + `N/M` 进度 + 逐项点亮）。
- **思考下沉**：思考文本从独立面板改为活跃子步骤下的行内 detail（复用打字机 reveal），定型后展开子流程可见全文；收敛/移除独立 ThinkingPanel。
- **注册式扩展**：新建 `agentSubflows.js` 注册表（主阶段 ↔ agent ↔ 子步骤）；新增 agent = 新增注册条目 + 路由其事件。
- **子步骤数据源复用**：①/③/⑥ 子步骤由**已透传的 agent 事件**驱动（perceive/analyze/plan/decide、generate/thinking/token/memory）；② 借 meta.questionKps + perceive 事件占位；不新增后端事件。
- **协议（可选，拆 agent 时必做）**：agent 事件增加可选 `agent` 路由字段（additive），使两个独立 agent 的事件可区分归属。

## Impact（阶段三）

- **前端（主，纯前端）**：新建 `agentSubflows.js`；`useTutoringSession`（handleAgent/handleThinking 推进子步骤 + detail、`agentFlow` 快照含子步骤）；`AgentTurnFlow` 渲染嵌套子流程；`ChatThread` live 走查同步嵌套；收敛/移除 ThinkingPanel。
- **后端 / Python（可选，当前零改动）**：仅当拆独立 agent 时，`agent_events.agent_event` 加 `agent` 字段 + Java 透传（均 additive）。阶段三本体不依赖。
- **数据契约**：`agentFlow` 快照扩展 `subSteps`（前端内部，消息持久化）；agent 事件可选 `agent` 字段（未来）。
