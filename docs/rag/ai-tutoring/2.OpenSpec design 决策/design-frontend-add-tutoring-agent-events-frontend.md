## Context

后端 `tutoring-agent-events` 变更已完成(decide SSE 消费、guardrail/memory 注入、generate agent 中继),SSE 事件序列从 `meta → token* → done` 变为:

```
agent(guardrail) → meta → agent(generate) → token* → agent(memory) → done
```

- `agent(guardrail)`(安全把关,status=done,detail="放行: hint" 或 "拒绝: reveal → 降级 approach")由 Java 护栏通过后、generate 前注入,在 `meta` **之前**
- `agent(generate)`(生成中,status=processing)由 Python generate 流透传,在首个 token 前
- `agent(memory)`(记忆更新,status=done,detail 汇总掌握度信号如"二元一次方程组 → 练习中")由 Java 落库后注入,在 `done` 前
- 终止/轮次上限场景**无 guardrail 事件**(无 generate 路径)
- decide 阶段事件(perceive/analyze/plan/decide)**不中继前端**

前端当前状态:`readSSE` 对未知事件 `default: break`(向后兼容),`useTutoringSession` 在 SENDING 阶段(等待 meta)仅显示打字 dots,40s+ 等待是黑盒。事件格式 `{level,stage,label,status,detail}`,level 恒 `sub`。

## Goals / Non-Goals

**Goals:**
- 消费 `event: agent`,渲染答疑思考流程(阶段 chips 流),把等待黑盒变可见进展
- chips 行独立于消息列表渲染,覆盖 guardrail(meta 前)→ generate → memory(done 前)整个 busy 周期
- agentStages 瞬态、不持久化;未知 stage 忽略(协议 additive,向后兼容)
- 不影响既有会话状态机/持久化/换题/结束判定逻辑

**Non-Goals:**
- 不渲染 decide 阶段事件(后端不中继,前端仅在 guardrail 前显示通用"AI 思考中")
- 不改 SSE 序列解析以外的任何协议(meta/token/done/error 语义不变)
- 不把 agentStages 写进 localStorage / 历史会话快照
- 不改变 KpChips 的累积逻辑(与 memory detail 信息重叠但分层展示)

## Decisions

### D1. readSSE 增加 `case 'agent'` 分发

**选择**: 在现有 `switch(currentEvent)` 增加 `case 'agent': handlers.onAgent?.(data); break`,并同步更新文件头部 SSE 协议注释。

**原因**: 与 meta/token/done/error 同模式,改动最小;streamRequest/streamFormRequest 已透传 handlers 对象,无需改动。

### D2. agentStages 状态模型:按 stage 去重、就地更新

**选择**: hook 新增 `agentStages`(数组)+ `agentStagesRef` 同步 ref。`handleAgent` 按 `data.stage` 去重:已存在 → 就地更新 status/label/detail(processing→done);不存在 → 追加到尾部(保持阶段插入顺序)。返回 `agentStages`。

**原因**: 同一 stage 会先 processing(如 generate)后 done;按 stage 合并保证每个阶段一个 chip、状态推进而非堆叠。插入序即视觉顺序。

**备选(放弃)**: 追加式数组(每个事件一个 entry)。同一 stage 会出现两个 chip(processing + done),视觉冗余。

### D3. chips 行独立于消息列表渲染

**选择**: `AgentStages` 组件在 `ChatThread` 内、消息流**末尾**(打字指示上方)渲染,条件为 `isPending || (isStreaming 且 agentStages 非空)`。不挂载到 AI 消息气泡上。

**原因**: `agent(guardrail)` 在 `meta` 前到达,此时 AI 气泡骨架尚未创建(phase=SENDING);只有独立渲染才能让 guardrail chip 先于气泡出现。位置放在消息流末尾而非最顶部:发送后用户视线在底部(新回复即将形成处),占位与 chips 应出现在新内容所在的区域(与打字指示同区),避免"AI 思考中"出现在整段历史消息上方造成错位感。chips 行跨 SENDING→STREAMING 持续存在,busy 结束(done/error)即消失。

### D4. chips 与打字 dots 共存

**选择**: SENDING 阶段 dots(等待 meta)保留,chips 行在其上方独立推进。两者不冲突:dots 表达"AI 尚未定稿回复骨架",chips 表达"AI 正在哪个阶段"。

### D5. memory detail 仅做 chip tooltip,KpChips 照旧

**选择**: `agent(memory)` 的 detail("二元一次方程组 → 练习中")渲染为 memory chip 的 `title` hover 提示;KpChips 继续由 `meta.eval.masterySignals` 在 done 后累积更新,两处都展示。

**原因**: 阶段条是过程感(本轮记忆已更新),chips 是结果态(会话累积掌握度),信息分层不冗余。

### D6. agentStages 瞬态、不持久化

**选择**: turn 开始(send/sendWithImage/requestAnswer/retryLast 置 SENDING)重置为空;done/error/终止/归档清空。不写入 localStorage、不参与历史快照。

**原因**: 阶段是过程性状态,恢复会话时无意义(重放阶段条反而误导)。

### D7. 未知 stage 忽略 + status 三态渲染

**选择**: `AgentStages` 对未知 stage 不渲染(协议 additive,后端未来可能加 tool/decide 阶段);已知 stage 按 status 渲染:done → "✓ label"、processing → "label…"(脉动)、error → "⚠ label"。

### D8. thinking 推理流:随 AI 消息存储 + 可折叠面板

**背景**: 后端 `tutoring-agent-events` 新增 `event: thinking`(模型豆包 seed 2.0 思考模式推理分片,agent(generate) 后、token 前,真实 62×分片)。decide 阶段(~17-48s)仍不中继,但 generate 的 thinking 把等待变可见(DeepSeek/Kimi 式"思考中")。

**选择**:
- `readSSE` 加 `case 'thinking'` 分发 `onThinking(data.content)`(协议 additive,无 onThinking 自然忽略)
- hook:`startAiMessage` 为 AI 消息加 `thinking: ''` 与 `thinkingActive: false` 字段;`handleThinking` 追加到当前流式 AI 消息;4 个发送函数挂 `onThinking`;thinking **随消息持久化**(localStorage 历史可回看推理)
- `thinkingActive` 契约对齐(**2026-08-13 演进:改为分片驱动**):由**实际收到的 thinking 分片**置位(`handleThinking` 追加分片时 `thinkingActive=true`),**不再由 `agent(generate)` 置位**。折叠条在首片到达即显示"思考过程"可展开;首片前不显示空占位
- 历史链路:`toMessage` 映射 `thinking: m.thinking || ''`;对账合并 server `recentMessages[].thinking`(`merged.thinking` + `thinkingActive=true`)
- UI:新组件 `ThinkingPanel`(默认收起 → 仅"思考过程"头部;展开 → 分片实时追加 + 自动滚底 + 打字机逐字 reveal;thinking 为空且非 active 不渲染)渲染在 MessageBubble 正文上方

**原因**: thinking 与 token 同属生成产物,挂在 AI 消息上最自然(无需独立瞬态状态),且持久化让 DeepSeek 式回看成为可能。`thinkingActive` 由分片驱动,使**关思考模式**(后端不吐 thinking)下面板自动隐藏、不显示空占位——兼容性关键(见 D10)。

**备选(放弃)**: thinking 作瞬态状态(done 后丢弃)。历史无法回看推理,与"思考模式"产品定位不符;挂消息字段仅多一个字符串,成本可忽略。首片空窗用"全局 thinking 数组非空即显示"判断——换题/降级轮无法区分,故用 `thinkingActive` 而非全局。

**边界**: 无 thinking(关思考模式 / 换题 / 降级)→ `thinkingActive` 恒 false、面板不渲染,行为与改造前一致。

### D9. decide thinking 瞬态缓存 + 实时思考条(后端 D7 配套,2026-08-13)

**背景**: 后端 D7 演进后,decide 阶段(17~48s)的 `event: thinking` 实时透传前端。但 decide thinking 到达时 phase=SENDING、**AI 消息尚未创建**(meta 才建),现有 `handleThinking` 的"追加到当前流式 AI 消息"守卫(`next[idx].role==='ai' && isStreaming`)会**丢弃** decide 分片。

**选择**:
- `useTutoringSession` 新增瞬态 `decideThinking`(字符串)+ `decideThinkingRef`(同步 ref),**不持久化**(与 agentStages 同,不入 localStorage/历史快照)
- `handleThinking` 分派:当前无流式 AI 消息(decide 阶段)→ 追加到 `decideThinking`;有流式 AI 消息(generate 阶段)→ 沿用现有追加到消息 `thinking`
- `handleMeta` 创建 AI 消息时(`startAiMessage`),把 `decideThinking` 注入新消息 `thinking` + `thinkingActive=true`,随后清空 decideThinking
- 清空时机与 agentStages 一致:turn 开始(send/sendWithImage/requestAnswer/retryLast 置 SENDING)、resetState、done/error/archive、TERMINATED 分支
- UI:`ChatThread` 在 SENDING 期、AgentStages("AI 思考中…")下方,渲染复用 `ThinkingPanel` 的实时思考条(`thinking=decideThinking, streaming=decideThinkingActive, active=true`),decide thinking 逐片流入;meta 到达后 AI 消息自带面板接管,瞬态条卸载

**原因**: decide thinking 归属"尚未存在的 AI 消息",瞬态缓存是最小侵入——不动消息模型/持久化/对账,与 agentStages 同生命周期模式。复用 ThinkingPanel 保持 DeepSeek 风格一致性,无需新组件。

**备选(放弃)**: decide 阶段提前创建 AI 消息草稿承接 thinking。改动消息生命周期(SENDING 期即有 AI 气泡)、影响空状态/换题/终止多分支,侵入大;瞬态缓存仅在 SENDING 期生效,meta 到达即归并,更稳。

**边界**: 换题/降级无 thinking → `decideThinking` 恒空、思考条不渲染;decide 失败(start 阶段重抛)→ decideThinking 随 turn 清空,无残留。

### D10. 兼容关思考模式(thinking 有则展示、无则隐藏,2026-08-13)

**背景**: 模型端 2026-08-12 拍板**全关思考模式**并切 `doubao-seed-2-0-mini`——`reasoning_content` 不返回,`thinking` 事件**取消**;耗时大幅缩短(decide ~1.5s / generate ~1.2s / 看图 ~3.4s,原 17~48s / 6.5s+ / 50~145s)。但产品后续**可能重开思考**,前端须兼容两种模式。

**选择**: 不删除 thinking 功能(开思考时直接可用),改为**数据驱动自动隐藏**:
- `thinkingActive` 由 thinking 分片驱动(见 D8 演进):后端不吐 thinking → `handleThinking` 不触发 → `thinkingActive` 恒 false → `ThinkingPanel` 显示条件 `hasThinking || (streaming && active)` 不成立 → 面板自动隐藏;`decideThinking` 恒空 → 实时思考条不渲染
- 不再由 `agent(generate)` 置位 `thinkingActive`(原来会在无 thinking 时显示"思考中…"空占位,与关思考冲突)
- AgentStages 阶段 chips 照常(agent 事件不依赖 thinking,是主要进度展示)
- 静默期占位简化:关思考后 decide ~1.5s,无需长等待动画/脉动;保留 AgentStages 的轻量"AI 思考中…"即可

**原因**: 前端不改模型/后端,纯前端数据驱动判断——"有 thinking 才展示"天然兼容开关两种状态。开思考时首片到达即激活面板(打字机逐字 reveal),关思考时无任何残留。

**备选(放弃)**: 硬编码移除 thinking 功能(按 2026-08-12 通知"移除思考面板")。开思考需重新开发,违背"后续需要思考"的规划;数据驱动自动隐藏零成本达成同样效果。

**边界**: 开思考时 thinking 分片到达 → 面板激活展示;关思考时 → 全程隐藏,仅 AgentStages chips + token 打字机,行为与无思考模式一致。

## Risks / Trade-offs

- **[R1] guardrail 事件在 meta 前,若 chips 行未及时挂载会闪失** → 缓解:D3 让 chips 行由 busy 驱动、独立渲染,guardrail 一到即插入;turn 开始就预留"AI 思考中"占位
- **[R2] memory detail 与 KpChips 信息重叠引起困惑** → 缓解:D5 分层(过程感 vs 结果态),detail 只做 tooltip 不铺开
- **[R3] 后端若未来中继 decide 阶段事件**,前端 chips 行自动多出阶段 → 缓解:additive 渲染 + 未知 stage 忽略,无需改动
- **[R4] 终止/轮次上限场景无 guardrail** → chips 行仅有"AI 思考中",turn 结束即清,行为符合预期
- **[R5] decideThinking 与消息 thinking 归并时的时序竞态** → 缓解:decide thinking 恒在 meta 前到达(后端 D7 `Flux.concat` 保证),meta 到达时 decideThinking 已完整,注入无竞态;若后端未来乱序,注入半段 thinking 也可接受(瞬态展示不落库)
- **[R6] 思考条与"AI 思考中"占位双显** → SENDING 期 AgentStages 占位 + decideThinking 思考条并存 → 缓解:占位是阶段 chips,思考条是推理内容,信息分层不冲突;decide thinking 为空时思考条不渲染,回到纯占位

## Migration Plan

1. `readSSE` 加 agent/thinking 分发 + 注释 → 单测/构建验证
2. hook 加 agentStages + handleAgent/onAgent;AI 消息 thinking/thinkingActive + handleThinking/onThinking
3. 新组件 `AgentStages` + `ThinkingPanel` + `ChatThread`/`MessageBubble`/`AiQa` 渲染接线
4. **D8 演进 + D10:thinkingActive 改由分片驱动(handleThinking 置位)、移除 agent(generate) 置位** → 兼容关思考模式(面板自动隐藏);thinking 打字机 reveal + 静默脉动提示
5. **D9:decideThinking 瞬态缓存 + handleThinking 分派 + meta 注入 + ChatThread 实时思考条**(开思考时生效;关思考时恒空自动隐藏)
6. 与后端联调:关思考模式(现状)验证无 thinking 面板、chips + token 打字机正常;若后端重开思考,验证 thinking 面板自动出现并逐字 reveal
7. build + openspec validate

回滚:纯前端 additive 改动,`onAgent`/`onThinking` 分发移除即可回到忽略事件;无后端契约破坏。D10 数据驱动隐藏——后端关思考时面板天然不渲染,后端开思考时自动恢复,无需回滚代码。

## Open Questions

- 前端是否要渲染 `agent(memory)` 的 detail 为可见文案而非仅 tooltip?本轮按 D5 只做 tooltip,若产品要求铺开再改。
- thinking 全文限高:展开区 `max-h-48` 滚动,超长推理(数百字)是否要给"全文展开/复制"入口?本轮无,产品需要再加。
- decide thinking 是否要给独立 UI(区别于 generate 思考面板)?本轮复用 ThinkingPanel 实时条,meta 后并入消息面板;产品若要求"决策 vs 生成"分段展示再拆。
- 关思考模式下 thinking 面板整体隐藏,是否需在 UI 上提示"当前为快速模式"?(非必须,AgentStages chips 已展示阶段进度)
