# design-backend-tutoring-agent-events

> summary: 解决decide响应式中继问题，优化流式事件返回逻辑
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D7. decide thinking 响应式中继（演进 D1，2026-08-13）
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-events
> 类别：架构设计

---

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
