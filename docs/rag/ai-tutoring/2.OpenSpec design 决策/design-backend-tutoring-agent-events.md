## Context

当前 Java 答疑编排（`ai-tutoring` 变更落地）：`decide`（非流式 JSON 返回 ActionMeta）→ Java 护栏 → `generate`（流式 SSE，Java 只透传 token）→ 前端。模型端已完成 `tutoring-agent-protocol` 变更并给出对接契约（`ai-edu-ai-service/docs/ai-tutoring-agent-events.md`）：

- **decide 响应从 JSON 改 SSE 流**：`agent(perceive/analyze/plan/decide)` → `meta(ActionMeta)` → `done`。Java 现在的 `bodyToMono(ActionMeta)` 会坏（**BREAKING**）。
- **generate 流新增 agent 事件**：`meta(action_type) → agent(generate) → token* → done`。
- **memory 归属已定**：由 Java 落库后发，Python 已删占位（不会双发）。
- 已定决策（2026-08 联调）：guardrail 文案"安全把关"、decide 流式后仅首事件前可重试 1 次、流中错误透传 error 不重试、短路/兜底分支同走 SSE 流。

Java 侧三个对接点：① decide SSE 消费（BREAKING）② generate 中继 agent 事件 ③ 注入 guardrail/memory 事件。`TutoringLlmClient.decide` 已按契约改了一半（SSE 解析 + `readActionMeta`），编排层注入尚未完成。

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

## Decisions

### D1. decide 消费：`bodyToFlux(SSE)` + 过滤 meta 事件（blockLast 同步取）

**选择**: 按模型端契约 §二，`decide()` 内部 `bodyToFlux(ServerSentEvent)` → `.filter("meta")` → `map(readActionMeta)` → `.next()` → `.block(decideTimeout)`。无 meta 事件（Python 发 `event: error` 或空流）→ 抛 `TutoringAgentException`（50005，会话保持）。

**原因**: 契约明确、改动最小（端口返回类型不变 `ActionMeta decide(ctx)`，编排层不用动）。decide 的 agent 阶段事件被丢弃（见 Non-Goals）。

**演进（2026-08-13，见 D7）**: D1 为上一阶段落地形态。因 decide 长等待（17~48s）是黑盒，演进为响应式中继 decide thinking（见 D7），decide 消费从"同步 blockLast 取 meta"改为"响应式中继 thinking + 提取 meta"。

### D2. guardrail 事件注入点：护栏通过后、generate 前

**选择**: `orchestrate` 返回流时 `Flux.concat(agent(guardrail), buildStream(...))`——guardrail 事件在 Java 自建 meta 之前发出。

**时序**: `agent(guardrail) → meta(Java) → agent(generate) → token* → agent(memory) → done`（与模型端文档时序一致）。

**detail**: `guard.isAllowed()` → "放行: {type}"；拒绝 → "拒绝: {type} → 降级 {fallbackType}"（如 "reveal 超限,降级 hint"）。terminate/round-limit 分支（无 generate）本轮不发 guardrail 事件（有各自终止语义）。

### D3. memory 事件注入点：落库完成后、流尾收尾信号

**选择**: memory 由 Java 发。真实落库（`applySideEffects` + `archiveTranscript`）发生在 `buildStream` 前；**memory 事件放流尾**（generate token 后、done 前）作为"本轮成果已记录"的收尾信号，视觉上"读取→思考→把关→生成→记忆"最顺。

**detail**: 汇总本轮 mastery 信号（如 "二元一次方程组 → 练习中"）；无信号时 detail=null。

**原因**: 视觉时序（tokens→memory→done）比真实落库时序（generate 前）更符合用户直觉；落库提前做，事件只是收尾展示。与模型端文档 §四 一致。

### D4. generate 中继 agent 事件

**选择**: `buildStream` 的过滤器从 `.filter(token)` 改 `.filter(token || agent)`，map 区分：token → 累积 AI 回复 + 透传；agent → 原样中继（`event: agent`）。Python generate 的 meta/done 仍丢弃（Java 自建）。

### D5. decide 重试/超时语义（流式后）

**选择**: `.retry(agentRetry)` 只在 Mono **error** 时触发（连接失败、未收到任何事件）。空流/`event: error`（Mono 正常完成无 meta）→ `.next()` 返回空 → null → 抛 TutoringAgentException，**不重试**（符合"已发事件后失败不重试"）。超时 = `.block(decideTimeout)` 等 meta 事件超时。

### D6. agent 事件格式

```json
event: agent
data: {"level":"sub","stage":"guardrail","label":"安全把关","status":"done","detail":"放行: hint"}
```

Java 侧用 `Map` + 现有 `SSE_MAPPER` 序列化（与 `contentToken` 同模式），新增 `agentEvent(stage, label, status, detail)` 帮助方法 + 阶段/文案常量。`level` 恒 `sub`（master 预留）。

### D7. decide thinking 响应式中继（演进 D1，2026-08-13）

**背景**: D1 的同步 `decide(ctx).block(...)` 使首轮 decide（实测 17~48s）成为黑盒——Java 在 decide 全部完成后才组装 SSE 响应返回，前端这段时间收不到任何字节，只显示"AI 思考中…"占位。而 Python decide 已在流式吐 `event: thinking`（decider.py 逐 delta `yield thinking`），全被 Java `.filter(meta)` 丢弃。

**选择**: decide 消费从"同步 blockLast 取 meta"演进为"响应式管线":

1. **端口改流式**: `TutoringLlmPort.decide(ctx)` → `decideStream(ctx): Flux<ServerSentEvent<String>>`（Python decide 原始事件流，thinking*/agent*/meta/done 全保留）。
2. **编排流式中继**（`orchestrate` 核心重构）:
   ```java
   Sinks.One<ActionMeta> metaSink = Sinks.one();
   Flux<ServerSentEvent<String>> decideThinking = llmPort.decideStream(ctx)
       .doOnNext(e -> { if ("meta".equals(e.event())) metaSink.tryEmitValue(readActionMeta(e.data())); })
       .filter(e -> "thinking".equals(e.event()));   // 只中继 thinking
   Mono<Flux<ServerSentEvent<String>>> tail = metaSink.asMono()
       .map(action -> postDecide(session, action, history, unlock));  // 护栏+副作用+generate
   return Flux.concat(decideThinking, Mono.from(tail).flatMapMany(f -> f))
       .onErrorResume(e -> handleDecideFailure(session, e));
   ```
   时序: `thinking*(decide) → agent(guardrail) → meta → agent(generate) → thinking*(generate) → token* → agent(memory) → done`。
3. **错误语义**: decide 流中途失败 → `onErrorResume` → 已有会话 `friendlyErrorStream`（50005，会话保持 ACTIVE）；start 阶段（session.id==null）重抛由接口层映射。
4. **并发锁适配**: 现 `withSessionLock` 同步持锁（decide+副作用后释放、generate 在锁外）。流式化后 decide 在 Flux 内执行 → 锁改为**订阅时获取、meta 副作用完成后释放**（`unlock` 参数传入 orchestrate，`postDecide` 副作用完成后调用；错误路径 `doFinally` 兜底）。
5. **decide agent 事件仍不透传**: `filter` 只放行 thinking，perceive/analyze/plan/decide 丢弃（与 D1 Non-Goals 一致）。（⚠️ 2026-08-12 **已演进**：filter 放行 `thinking + agent`，见 `tutoring-agent-workflow-backend` change design D1）

**原因**: thinking 与 token 是并行内容流，decide 决策思考正是主等待段（17~48s）；实时中继把黑盒变可见，与 generate thinking 的 DeepSeek 风格一脉相承。代价是 orchestrate 从"同步 decide→同步编排"改"响应式管线"，terminate/round-limit/副作用分支挪进 `postDecide`（复用原逻辑，仅执行时机从返回流前变为 meta 到达后）。

**不入库**: decide thinking 仅实时透传，历史消息 thinking 仍只存 generate 段（避免改 Redis/COS 消息模型 + 历史渲染契约）。产品若要求决策思考也回看，另立 change。

**备选（放弃）**: 维持 D1 同步 blockLast（现状黑盒，用户已反馈体验问题）；decide thinking 累积后一次性重放（仍是"思考完才展示"，不解决流式诉求）。

## Risks / Trade-offs

- **[R1] decide agent 阶段事件不可见**：前端看不到"读取题目/解析意图/规划引导/决策"四阶段 → 缓解：decide thinking 已实时中继（D7），用户能看实时推理而非黑盒；perceive/analyze/plan/decide 阶段标签仍不展示（产品要求再补）
- **[R2] memory 事件与真实落库时序错位**：落库在 generate 前、事件在流尾 → 缓解：事件只作展示信号，detail 如实反映已完成的落库；落库失败（异常）时整轮已降级，无 memory 事件
- **[R3] generate 透传 agent 事件后前端契约变化**：新增 `event: agent` → 缓解：协议 additive，旧前端忽略未知事件即可；api.md 明示新事件序列
- **[R4] decide 空流/error 的边界**：decideStream 无 meta / 中途 error → 缓解：`metaSink` 收 error 或流完成未出 meta 均按失败处理，`onErrorResume` → 50005 降级，会话保持 ACTIVE
- **[R5] decide 响应式重构的回归面**：orchestrate 从同步 decide 改响应式管线，terminate/round-limit/副作用/锁全部重排 → 缓解：`postDecide` 抽取原逻辑不改决策；单测覆盖正常流/终止/轮次上限/失败路径；锁改为订阅时取、副作用后释放，行为等价
- **[R6] decide thinking 不入库**：刷新后首轮思考条消失（仅实时） → 缓解：明确列为决策；产品要求回看则另立 change 落库

## Migration Plan

1. `TutoringLlmClient.decide` SSE 解析（已完成一半）→ 编译验证
2. `TutoringAppService` 注入 guardrail/memory + generate agent 中继 → 单元测试
3. **D7 演进：decide 改流式端口 + orchestrate 响应式中继 thinking + postDecide 抽取 + 并发锁适配** → 单测（含 thinking 先于 guardrail 时序断言）
4. 与模型端联调：真实 decide/generate SSE 事件序列（decide thinking 实时透传）
5. 更新 api.md（新事件序列）+ test.md（实测事件覆盖）
6. 前端接入 `event: agent` 渲染 + decide thinking 瞬态缓存（前端侧，协议已透传）

回滚：decide 契约是模型端已改的 BREAKING，Java 端无法独立回滚（旧 JSON 消费已失效）；若需回退，需模型端切回旧契约。D7 演进为 additive（多中继 thinking 事件），可回退到 D1 同步消费。

## Open Questions

- **decide 的 agent 阶段事件（perceive/analyze/plan/decide）要不要实时中继前端？** 目前只中继 thinking（D7），阶段标签不展示；若产品要"决策四阶段"过程感，在 D7 的响应式管线里多 filter 一层 agent 事件即可，单独排期。（✅ 已答复 2026-08-12：**要**，`tutoring-agent-workflow-backend` 已实现 filter 放行 agent + 前端"本轮意图"面板消费）
- **decide thinking 要不要落库？** 当前不入库（仅实时），刷新后消失；产品若要求历史回看决策思考，需扩展 Redis/COS 消息模型，另立 change。
- **guardrail 事件的 terminate/round-limit 分支**是否也要发？本轮不发（D2），如产品要求"拒绝也要展示把关"再补。
- 前端对 `event: agent` 的渲染粒度（进度条 vs 标签流）由前端侧定。
