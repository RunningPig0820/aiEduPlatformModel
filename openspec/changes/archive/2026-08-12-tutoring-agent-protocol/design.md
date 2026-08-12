## Context

AI 答疑当前是**两调用架构**(`ai-tutoring` 变更已落地):`decide`(非流式返回 ActionMeta)→ Java 护栏 → `generate`(流式 SSE)。Java 拥有数据(掌握度/图谱/会话)并做护栏审批;Python 无状态、纯智能。

三个驱动本次改造的现实:

1. **等待黑盒**:每次 1-2 分钟才有答案,用户面对黑盒等待,无法感知进展。
2. **答疑要成为"子 agent"**:最终愿景是**主 agent + 多领域子 agent**(答疑 / 知识图谱 / 错题集 / 批改)。答疑必须先做成接口稳定、可插拔的子 agent,将来主 agent 才能直接编排。
3. **分工原则**:Python = 决策智能(思考/生成),Java = 把关(护栏)+ 流程控制 + 前端对接 + 数据提供。

## 目标架构(改造后)

```
┌─ 前端 ─────────────────────────────────────┐
└──────────────┬─────────────────────────────┘
               ▼ 透传 agent 事件 / token
┌─ Java(把关 + 流程 + 前端对接 + 数据提供)──────┐
│  ① 中继 Python 的 agent 事件给前端           │
│  ② 发把关事件: agent(guardrail) 安全审批      │
│  ③ 发记忆事件: agent(memory) 掌握度落库/点亮  │
│  ④ 护栏规则: reveal/轮次/安全/换题            │
│  (将来) 提供工具接口: 掌握度查询/保存          │
└──────────────┬─────────────────────────────┘
               ▼ 调用 decide/generate
┌─ Python(答疑子 agent: 决策智能 + 思考展示)─────┐
│  decide(流式):  agent(perceive)→analyze→plan  │
│                 →decide → meta(ActionMeta)    │
│  generate(流式): agent(generate)→ token* →    │
│                 agent(memory)→ done           │
│  (将来) 主动调知识图谱 agent(工具阶段)          │
└──────────────────────────────────────────────┘
```

**将来演进**(本次不实现):

```
主 agent(编排)
  ├── 答疑 agent ← 本次改造的就是它
  ├── 知识图谱 agent(知识点查询/保存/点亮)  ← 将来,答疑通过工具调它
  ├── 错题集 agent                         ← 将来
  └── 批改 agent                           ← 将来
```

## Goals / Non-Goals

**Goals:**
- 定义 **agent 事件协议**(标准事件格式 + 标准阶段表),答疑子 agent 全程发射思考阶段事件
- decide 改流式:发射 感知→解析→规划→决策 阶段,`meta` 事件携带 ActionMeta(内容不变)
- generate 加 agent 阶段事件(生成中/记忆)
- Java 发把关/记忆事件(护栏审批、掌握度落库)—— 展示 Java"守门"动作
- 事件协议支持两层嵌套(`level: master/sub`),为主 agent 预留
- 把答疑做成**接口稳定、可插拔的子 agent**(契约是它作为子 agent 的边界)

**Non-Goals:**
- **不实现真工具调用**(知识图谱 agent 是将来独立的子 agent;`tool` 阶段仅协议预留)
- 不建主 agent
- 不建知识图谱 / 错题集 / 批改 agent
- 不改变 ActionMeta 契约内容、不改变生成内容约束(引导式学习不变)

## Decisions

### 1. decide 从非流式改流式(SSE)

**选择**: `POST /api/tutoring/decide` 响应从 `ActionMeta`(JSON)改为 SSE 流:先发 agent 阶段事件,再发 `meta`(携带 ActionMeta),最后 `done`。**BREAKING**(Java 消费方式从"读 JSON"改为"解析 SSE 流提取 meta 事件")。
**原因**: 决策展示归 Python(分工原则),decide 不流式就无法展示它的思考阶段;将来工具层使 decide 变多步时,流式契约一步到位。
**备选**: decide 保持非流式,Java 发占位标签 —— 契约不动,但阶段展示在 Java,与"Python 控制决策展示"相悖,且将来仍要改。

### 2. agent 事件协议(标准格式 + 标准阶段表)

```json
event: agent
data: {
  "level": "sub",            // sub=子agent | master=主agent(将来)
  "stage": "plan",           // 标准阶段
  "label": "规划引导方案",    // 前端展示文案
  "status": "processing",    // processing | done | error
  "detail": "..."            // 可选(工具结果/决策摘要)
}
```

标准阶段表(所有子 agent 共用):

| stage | 含义 | 现在真实 or 占位 | 发射方 |
|-------|------|----------------|--------|
| `perceive` | 感知输入 | ✅ 真实 | Python |
| `analyze` | 意图/需求解析 | ⚠️ 占位(在 decide 调用内) | Python |
| `plan` | 规划任务 | ⚠️ 占位 | Python |
| `tool` | 工具调用 | 🔮 将来(知识图谱 agent) | Python(预留) |
| `decide` | 决策完成 | ✅ 真实 | Python |
| `generate` | 生成中 | ✅ 真实 | Python |
| `memory` | 记忆更新 | ✅ 真实 | Java(落库) |
| `guardrail` | 安全把关 | ✅ 真实 | Java |

**占位阶段为何入协议**: 协议按最终形态设计——将来 decide 拆多步/工具层上,占位变真实,协议不改。

### 3. Java 发把关/记忆事件(展示"守门")

Java 在它真实执行的动作点发事件:
- **guardrail**: 读完 decide 的 `type` + 计数,过护栏规则(要答案上限/轮次/安全 flag/换题)后发 `agent(guardrail)`。Java 只读 type+count 不看对话(防提示词攻击的核心)。
- **memory**: 收到 mastery_signals,解析 kp_label→URI、落 t_student_kp_mastery、点亮图谱、归档会话后发 `agent(memory)`。

**原因**: Java 的"把关"是真实且关键的平台动作,展示它 = 前端看到"Python 在想、Java 在守门",符合分工原则。

### 4. 工具阶段(tool)协议预留,不实现真工具

事件协议包含 `tool` 阶段与字段,但本次**不接入真实工具**。答疑子 agent 作为可插拔单元的边界是稳定的契约(decide/generate/ActionMeta);将来知识图谱 agent 建成后,答疑通过工具调用它(模型主动触发,见 Context 中的演进)。

### 5. 两层嵌套(level: master/sub)

协议含 `level` 字段,为主 agent 预留:主 agent 的思考阶段(解析意图→选 agent→编排)与子 agent 的思考阶段(感知→...→记忆)可嵌套展示。本次只有 `sub` 层。

### 6. 空流兜底保留

generate 零 token 时给固定引导话术(已实现于 `ai-tutoring`),避免空回复。

### 7. Java 对接细节(2026-08 后端联调确认)

- **memory 事件归属: Java 发,Python 不发占位**。Python generate 流只有 meta/agent(generate)/token*/done;Java 在真实落库(掌握度/图谱点亮/归档)完成后发 `agent(memory)`。避免双发。
- **decide 重试/超时(流式后)**: 仅"未收到任何 SSE 事件"时(连接阶段)可重试 1 次(无副作用);已收到 agent 事件后失败 → 不重试,透传 error,Java 降级。超时 = 等待 meta 事件到达的超时。
- **guardrail/memory 触发点**: guardrail = Java 护栏审批通过后、调 generate 前(文案"安全把关",detail 可带拒绝摘要);memory = Java 落库完成后(文案"记忆更新")。
- **短路/兜底分支流式**: is_new_question 短路、degraded 兜底均走同一 SSE 流(meta 携带对应 ActionMeta),Java 从 meta 取 type 走护栏,逻辑不变。
- **decide 流中错误**: Python 发 `event: error` → Java 透传前端,**不重试**(已发部分 agent 事件,重试会重发);对外 40004"网络波动",会话保持。

### 8. 保留思考模式,新增 `thinking` 事件(2026-08)

**背景**: 后端反馈 decide 耗时 17~48s(豆包默认开思考),提议关闭思考降耗时。**产品拍板:不关思考,
把真实推理过程流式展示出去**(decide + generate 都展示)——黑盒等待变可见,符合"思考过程展示"目标。

**实现**: langchain-openai 流式解析会**丢弃 reasoning_content**(实测 additional_kwargs 也为空),故
decide/generate 的流式主路径改为**直连方舟读原始 SSE**(`core/tutoring/ark_stream.py`,httpx),
`reasoning_content` → 新事件 `event: thinking`(与 token 同构的内容流),前端可折叠展示。

**契约影响**: `thinking` 是附加事件,Java 零改动(decide 过滤 meta 时忽略;generate 直接透传)。
降级路径: 原始流失败/args 非法 → 降级现有非流式四段管线(该次无 thinking,罕见)。

### 9. ChatTurn 容忍附加字段(extra='ignore',2026-08)

Java 在历史消息上附加 `thinking` 字段(仅 Java 存储/前端展示用),会出现在 decide/generate 请求里。
`ChatTurn` 显式 `model_config = ConfigDict(extra="ignore")`,固化"容忍附加字段"契约:

- 该字段在 Pydantic 校验时被剥离,**不进请求模型**
- 提示词渲染(`_format_history`)只读 role/content/image_url → **thinking 永不进 LLM prompt**(避免模型看到自己旧推理偏置)
- 显式声明防未来误开 `extra='forbid'` 严格模式导致校验失败
- 回归测试: `test_models.py`(ChatTurn 附加字段 + 请求级 history 带 thinking 校验通过)

## Risks / Trade-offs

- **[R1] decide 契约 breaking**: Java 需一次性改造(解析 SSE 流提取 meta)。动作明确、范围可控,但联调需同步。
- **[R2] 占位阶段的真实性**: analyze/plan 在 decide 单次调用内,只能发占位(调用返回前不可见)。阶段感主要靠"每步可见"缓解等待,真实多步要等工具层。
- **[R3] 事件协议设计前置**: 为主 agent / 工具层预留 `level`/`tool` 字段,有过度设计风险;但成本低、避免将来返工。
- **[R4] Java 事件与 Python 事件的时序协调**: guardrail/memory 事件由 Java 插入到 Python 事件流中,需 Java 侧保证顺序(decide 后、generate 前等)。

## 与 ai-tutoring 变更的契约衔接(2026-08 确认)

本变更是 `ai-tutoring` 的演进,衔接点:
- **ActionMeta 契约不变**(闭集 type/eval/mastery_signals/new_question/end_reason/summary/safety_flag/degraded)——decide 流式化只改响应"载体"(JSON→SSE 的 meta 事件),字段不变
- **请求契约不变**(DecideRequest/GenerateRequest,含 `is_new_question`、image_url 图片通道)——新增的 agent 事件是附加事件,不改请求
- **BREAKING 仅一处**: decide 响应从 JSON 改 SSE 流(Java 消费方式改,见 `docs/ai-tutoring-agent-events.md`)
- 旧文档已标注演进:`ai-tutoring/api.md`(decide 段)、`ai-tutoring/design.md`(决策 2)、`docs/ai-tutoring-agent.md`(3.1 段)

## Open Questions

- 主 agent 何时建、是否用 LangGraph(将来,编排层才需要图)
- 知识图谱 agent 的工具接口形状(将来,`query_mastery`/`save_mastery` 等,需 Java 提供数据接口)
- guardrail/memory 事件的具体触发点与文案,需 Java 侧确认
