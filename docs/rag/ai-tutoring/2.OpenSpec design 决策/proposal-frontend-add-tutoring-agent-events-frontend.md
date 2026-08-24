## Why

后端 `tutoring-agent-events` 变更已在答疑 SSE 流新增两类事件,把 40s+ 的等待黑盒变成可见进展:
- **`event: agent`**(阶段事件:guardrail 安全把关 / generate 生成中 / memory 记忆更新),序列从 `meta → token* → done` 变为 `agent(guardrail) → meta → agent(generate) → token* → agent(memory) → done`
- **`event: thinking`**(模型豆包 seed 2.0 思考模式推理分片,agent(generate) 后、token 前,真实 62~71 分片),DeepSeek/Kimi 式"思考中"体验

**2026-08-12 演进**:模型端拍板**全关思考模式**并切 `doubao-seed-2-0-mini`,`thinking` 事件取消(耗时从 17~48s / 6.5s+ 降至 ~1.5s / ~1.2s);但产品后续**可能重开思考**。前端须**兼容两种模式**:thinking 有则展示、无则自动隐藏(见 What Changes D10)。

前端当前 `readSSE` 对未知事件 `default: break`(向后兼容,功能不受影响),但要兑现后端价值,需消费并渲染这两类事件。

## What Changes

- **`readSSE` 新增 `event: agent` 分发**:`handlers.onAgent?.(data)`,头部注释补 agent 协议文档(事件格式 `{level,stage,label,status,detail}` + 完整事件序列)
- **`useTutoringSession` 新增 `agentStages` 瞬态状态**:按 stage 去重就地更新(processing→done)、保持插入顺序、turn 开始重置、done/error/终止/归档清空;4 个发送函数(send/sendWithImage/requestAnswer/retryLast)挂 `onAgent`
- **新组件 `AgentStages`**:渲染阶段 chips 流(✓ 安全把关 / 生成中… / ✓ 记忆更新),status=processing 脉动、done 打勾、error 警示;detail 做 hover 提示;未知 stage 忽略(协议 additive);`waiting` 占位在 decide 等待期显示"AI 思考中…"
- **`ChatThread` 渲染接线**:busy 时在消息流末尾(打字指示上方)渲染 chips 行,独立于消息列表(guardrail 在 meta 前、AI 气泡未建),覆盖 SENDING→STREAMING 整个周期
- **`agentStages` 不持久化**(瞬态),localStorage 模型不变
- **`readSSE` 新增 `event: thinking` 分发**:`handlers.onThinking?.(data.content)`,协议注释补 thinking 位置(agent(generate) 后、token 前;decide 阶段 guardrail 前也有 thinking)
- **`useTutoringSession` 消息模型加 thinking**:AI 消息加 `thinking` 字段(`handleThinking` 实时拼接分片)+ `thinkingActive` 标记(**由 thinking 分片驱动置位**,不再由 agent(generate) 置位);thinking 随消息持久化;对账合并 server `recentMessages[].thinking`
- **新组件 `ThinkingPanel`**:可折叠"思考过程"面板(默认收起 / 展开实时追加自动滚底 / 打字机逐字 reveal / 无 thinking 不渲染),渲染在 `MessageBubble` 正文上方
- **decide thinking 瞬态缓存(D9)**:`useTutoringSession` 加 `decideThinking` 瞬态缓存——`handleThinking` 在无流式 AI 消息时(decide 阶段)追加到 decideThinking,meta 创建 AI 消息时注入消息 `thinking` 后清空;不持久化
- **SENDING 期实时思考条**:`ChatThread` 在 AgentStages 下方渲染复用 `ThinkingPanel` 的实时思考条,decide thinking 逐片流入;meta 后由 AI 消息面板接管
- **兼容关思考模式(D10)**:`thinkingActive` 由 thinking 分片驱动——后端关思考(无 thinking 事件)时面板/思考条**自动隐藏**,不显示空占位;开思考时首片到达即激活面板。thinking 功能整体保留,无需删除

## Capabilities

### New Capabilities
- `ai-tutoring-agent-events`: 答疑 SSE 阶段事件(`event: agent`)与推理流(`event: thinking`)消费与渲染——readSSE 分发、hook agentStages 状态机与 thinking 消息模型、AgentStages chips、ThinkingPanel 思考面板

### Modified Capabilities
<!-- 无:ai-tutoring 未提升为独立 root spec(后端同样注记),本变更覆盖其 SSE 协议扩展,作为新能力落档 -->

## Impact

- `ai-edu-front/src/api/modules/tutoring.js` — readSSE 加 `case 'agent'`/`case 'thinking'` + 协议注释
- `ai-edu-front/src/hooks/useTutoringSession.js` — `agentStages` 状态 + `handleAgent`/`onAgent`;AI 消息 `thinking`/`thinkingActive` 字段 + `handleThinking`/`onThinking`;对账合并 server thinking;`decideThinking` 瞬态缓存 + handleThinking 分派 + meta 注入
- `ai-edu-front/src/components/student/ai-qa/AgentStages.jsx` — 新组件(chips 流渲染 + waiting 占位)
- `ai-edu-front/src/components/student/ai-qa/ThinkingPanel.jsx` — 新组件(可折叠思考过程面板;SENDING 期实时思考条复用)
- `ai-edu-front/src/components/student/ai-qa/MessageBubble.jsx` — 正文上方渲染 ThinkingPanel
- `ai-edu-front/src/components/student/ai-qa/ChatThread.jsx` — busy 时渲染 AgentStages;SENDING 期渲染 decideThinking 实时思考条
- `ai-edu-front/src/pages/student/AiQa.jsx` — 解构 `agentStages`/`decideThinking` 传给 ChatThread
- 无 API 契约破坏(后端协议 additive,旧前端忽略 agent/thinking 事件照常工作;D9 依赖后端 D7 decide thinking 透传,后端未演进时 decideThinking 恒空、思考条不渲染)
