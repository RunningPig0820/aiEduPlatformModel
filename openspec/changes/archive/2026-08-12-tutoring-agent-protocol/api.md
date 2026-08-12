# 答疑子 agent 事件协议与 decide 流式契约

> 基于 `ai-tutoring` 变更的 decide/generate 端点,叠加 agent 思考流程展示。
> **BREAKING**: decide 响应从 JSON 改 SSE 流(Java 消费方式需改)。

## thinking 事件(思考过程展示,Java 零改动)

保留豆包思考模式,把模型真实推理 `reasoning_content` 作为**附加内容流**透传(与 token 同构):

```
event: thinking
data: {"content": "<推理分片>"}
```

- **decide 与 generate 都会吐**(决策推理 + 解题推理),前端用可折叠"思考过程"面板按 chunk 拼接
- **Java 零改动**: decide 消费只过滤 `meta` 事件(thinking 被忽略);generate 的 `Flux<SSE>` 直接透传

## agent 事件协议

所有 agent 阶段事件格式统一:

```
event: agent
data: {"level": "sub", "stage": "plan", "label": "规划引导方案", "status": "processing", "detail": "..."}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| level | String | `sub`(子 agent)/ `master`(主 agent,预留) |
| stage | String | 标准阶段:perceive / analyze / plan / tool / decide / generate / memory / guardrail |
| label | String | 前端展示文案(中文) |
| status | String | processing / done / error |
| detail | String? | 可选补充(工具结果、决策摘要等) |

### 标准阶段表

| stage | label | 发射方 | 真实/占位 |
|-------|-------|--------|-----------|
| perceive | 读取题目 | Python | 真实 |
| analyze | 解析意图 | Python | 占位(decide 调用内) |
| plan | 规划引导 | Python | 占位 |
| tool | 工具调用 | Python(预留) | 将来 |
| decide | 决策完成 | Python | 真实 |
| generate | 生成中 | Python | 真实 |
| memory | 记忆更新 | Java | 真实 |
| guardrail | 安全把关 | Java | 真实 |

## 1. decide(响应改 SSE 流式)

### 请求(不变)

`POST /api/tutoring/decide`,请求体 DecideRequest 与 `ai-tutoring` 一致。

### 响应(BREAKING: JSON → SSE)

```
event: agent  data: {"level":"sub","stage":"perceive","label":"读取题目","status":"done"}
event: agent  data: {"level":"sub","stage":"analyze","label":"解析意图","status":"processing"}
event: agent  data: {"level":"sub","stage":"plan","label":"规划引导","status":"processing"}
event: thinking  data: {"content":"学生已设出未知数..."}   ← 模型真实推理分片(可多条)
event: thinking  data: {"content":"..."}
event: agent  data: {"level":"sub","stage":"decide","label":"决策完成","status":"done"}
event: meta   data: {ActionMeta}        ← 决策结果,与改造前字段完全一致
event: done   data: {"model_used":"doubao/doubao-seed-2-0-lite-260428"}
```

Java 解析:读 SSE 流,提取 `meta` 事件 data 作为 ActionMeta(取 type/计数走护栏)。`thinking` 事件被过滤逻辑自动忽略。

### 错误(不变)

| HTTP | 说明 |
|------|------|
| 403 | 缺/错内部 token |
| 422 | 参数校验失败(流式前返回,不进 SSE) |

## 2. generate(加 agent 阶段事件)

### 响应(SSE,事件序列)

```
event: meta    data: {"action_type":"hint"}
event: agent   data: {"level":"sub","stage":"generate","label":"生成中","status":"processing"}
event: thinking  data: {"content":"先判断已知条件..."}   ← 模型推理(可多条,前端可折叠)
event: token   data: {"content":"..."}
event: token   data: {"content":"..."}
event: done    data: {"model_used":"..."}
```

> **memory 事件由 Java 发(不在 Python generate 流中)**: Python 不发占位(避免与 Java 真实落库双发)。Java 在 generate done 后、真实落库完成时发 `agent(memory)`。

零 token 时保留空流兜底话术(token 事件带固定引导语)。

## 3. Java 把关/记忆事件 + decide 重试/错误(时序)

```
Python decide: thinking* → agent(decide) → event: meta(ActionMeta) → done
        ↓
Java 护栏审批 → event: agent {"stage":"guardrail","label":"安全把关","status":"done"}
        ↓ 放行
Java 调 generate: 透传 event(generate/thinking*/token*/done)
        ↓
Java 落库完成 → event: agent {"stage":"memory","label":"记忆更新","status":"done"}
```

**decide 重试/超时(流式后)**: 仅当**未收到任何 SSE 事件**(连接阶段失败)可重试 1 次(无副作用,不会重发已见事件);已收到 agent 事件后失败 → 不重试,透传 `error`,Java 降级。超时 = 等待 `meta` 事件到达的超时(60s 内到 meta)。

**decide 流中错误**: Python 发 `event: error`(code/message)→ Java 透传前端 → 前端保留已显示阶段 + 错误提示。**不重试**(已发部分 agent 事件,重试会重发)。

**短路/兜底分支**: is_new_question 短路(meta type=switch)、degraded 兜底(meta type=hint, degraded=true)**均走同一 SSE 流**,Java 从 meta 事件取 type 走护栏(逻辑与之前一致)。

## 联调注意

1. **decide 是 BREAKING**: Java 消费从"读响应 JSON"改"解析 SSE 提取 meta 事件",一次性改造。
2. **事件顺序**: guardrail 在 decide 的 meta 之后、generate 的 meta 之前;memory 在 generate done 之前。
3. **两层嵌套**: 本次只有 `level=sub`;主 agent(将来)用 `level=master` 发自己的编排阶段。
