# AI 答疑 Agent 事件协议 —— Java 对接契约

> 对应 OpenSpec change `tutoring-agent-protocol`(Python 仓库)。本文件是**给 Java 团队的对接说明**,可直接转发。
> 对应 Java 侧 `TutoringLlmPort` / `TutoringLlmClient` / `TutoringAppService`。

## 〇、新增:`thinking` 事件(思考过程展示,Java 零改动)

**背景**: 保留豆包思考模式(不关闭),把模型真实推理 `reasoning_content` 作为**附加内容流**流式透传,
前端用可折叠"思考过程"面板展示(类似 DeepSeek/Kimi)。decide 和 generate 都会吐。

```
event: thinking
data: {"content": "<推理分片>"}     # 与 token 同构,前端按 chunk 拼接
```

**对 Java 的影响: 零改动。**
- decide 消费已改为"只过滤 `meta` 事件",`thinking` 事件会被 `.filter(e -> "meta".equals(e.event()))` 自动忽略,无需处理
- generate 的 `Flux<ServerSentEvent<String>>` 直接透传,`thinking` 事件随流到达前端
- 仅前端新增渲染(可选,不渲染则自动忽略)

## 一、总览:BREAKING + 两处事件注入

```
[Python decide] 现在返回 SSE 流(不再是 JSON)  ← ①BREAKING,Java 消费方式要改
[Python decide/generate] 流里新增 thinking*(模型真实推理) ← 附加事件,Java 忽略/透传即可
[Python generate] 流里已有 agent(generate)/token*/done
[Java] 需要: ② 护栏后注入 agent(guardrail)  ③ 落库后注入 agent(memory 完成)
```

## 二、① BREAKING:decide 从"读 JSON"改"解析 SSE 提取 meta"

**当前代码(`TutoringLlmClient.decide`)会坏:**
```java
// 现在(流式化后失效)
.bodyToMono(ActionMeta.class)   // ← 响应已不是 JSON,是 SSE 流
```

**改成:读 SSE,过滤 `meta` 事件,取它的 data 作为 ActionMeta**
```java
// 改后
ActionMeta meta = tutoringWebClient.post()
    .uri(config().decidePath())
    .contentType(MediaType.APPLICATION_JSON)
    .accept(MediaType.TEXT_EVENT_STREAM)
    .bodyValue(context)
    .retrieve()
    .bodyToFlux(new ParameterizedTypeReference<ServerSentEvent<String>>() {})
    .filter(e -> "meta".equals(e.event()))          // 只取 meta 事件
    .map(e -> jsonMapper.readValue(e.data(), ActionMeta.class))
    .blockLast(config().decideTimeout());            // 决策结果在 meta 事件里
```

**说明:**
- Python 现在发:`event: agent(perceive/analyze/plan) → event: thinking* → event: agent(decide) → event: meta(data=ActionMeta) → event: done`
- `thinking*` 是模型真实推理分片(可多条,最长可达 decide 全程,即原来 17~48s 的黑盒等待变可见)
- `meta` 事件的 data 就是 ActionMeta,字段与之前完全一致(闭集 type/eval/mastery_signals 等)
- decide 重试语义保留(Java 侧 `agentRetry` 逻辑不变,只是解析方式变了)
- **仅此一处 breaking**,generate/ocr 不动

## 三、② 护栏后注入 `agent(guardrail)` 事件

**位置**:`TutoringAppService` 里,decide 返回 ActionMeta → `TutoringGuardrailService` 审批通过后、调 generate 前。

```java
// 护栏审批通过后、generate 前,向响应流注入一个 guardrail 事件
agentEvent("guardrail", "安全把关", "done")
```

**事件格式**(与 Python 协议一致):
```json
event: agent
data: {"level":"sub","stage":"guardrail","label":"安全把关","status":"done","detail":"reveal拒绝/轮次/放行"}
```

**护栏逻辑不变**(只读 type+count,不看对话)——只是现在要把"审批完成"这个动作作为事件展示给前端。

## 四、③ 落库后注入 `agent(memory)` 事件

**已定(2026-08 后端联调): Java 发,Python 删占位。**

- Python generate 流**已删** `agent(memory)` 占位(只有 meta/agent(generate)/token*/done)
- Java 在真实落库(`TutoringKpResolver` 解析 URI + `t_student_kp_mastery` 更新 + 图谱点亮 + `TutoringTranscriptArchiver` 归档)完成后,向前端发 `agent(memory, 记忆更新, done)`

```
前端收到:
  ... token* → done ←(Python generate 流结束)
  agent(memory)      ← Java 落库完成后追加
```

## 五、Java 中继 agent 事件

`TutoringLlmClient.generate` 已返回 `Flux<ServerSentEvent<String>>`,agent 事件会在流里,Java **直接透传即可**(前端按协议渲染)。无需额外处理。

## 六、已定决策(2026-08 后端联调)

1. **memory 归属**: Java 发(落库后),Python 已删占位 —— 无双发。
2. **guardrail 文案**: "安全把关"(detail 可带拒绝摘要,如 "reveal 超限,降级 hint")。
3. **decide 重试/超时(流式后)**: 仅"未收到任何 SSE 事件"时可重试 1 次(无副作用);已收到 agent 事件后失败 → 不重试,透传 `error`,Java 降级。超时 = 等 meta 事件超时。
4. **decide 流中错误**: 透传 `event: error` 给前端,不重试,对外 40004"网络波动",会话保持。
5. **短路/兜底分支**: is_new_question 短路 / degraded 兜底均走同一 SSE 流,Java 从 meta 取 type 走护栏(逻辑不变)。

## 事件时序总览(改造后完整一轮)

```
前端 ◀── Java ◀── Python
  agent(perceive/analyze/plan)           ← Python decide(阶段占位)
  thinking* ...                          ← Python decide(模型真实推理,黑盒变可见)
  agent(decide)
  meta(ActionMeta)
  done
  agent(guardrail)                       ← Java 护栏(新)
  meta(action_type)                      ← Python generate
  agent(generate)
  thinking* ...                          ← Python generate(推理,前端可折叠展示)
  token* ...
  done
  agent(memory)                          ← Java 落库后发(完成)
```
