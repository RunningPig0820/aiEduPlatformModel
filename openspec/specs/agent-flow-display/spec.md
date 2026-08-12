# agent-flow-display Specification

## Purpose
TBD - created by archiving change tutoring-agent-protocol. Update Purpose after archive.
## Requirements
### Requirement: agent 思考流程事件协议

系统 SHALL 提供标准 agent 事件协议,答疑子 agent 在完整流程(感知→意图→规划→决策→生成→记忆)中发射阶段事件,供前端展示思考过程。

#### Scenario: 事件格式
- **WHEN** Python 或 Java 发射 agent 阶段事件
- **THEN** 事件格式为 `{level, stage, label, status, detail}`,其中 `stage` 属于标准阶段表(perceive/analyze/plan/tool/decide/generate/memory/guardrail),`status` 属于 processing/done/error

#### Scenario: 阶段覆盖
- **WHEN** 一次完整的答疑轮次执行
- **THEN** 发射的事件覆盖决策阶段(感知/解析/规划/决策)与生成阶段(生成/记忆),以及 Java 把关阶段(guardrail)

#### Scenario: 两层嵌套预留
- **WHEN** 事件协议包含 `level` 字段
- **THEN** `level=sub` 表示子 agent 阶段;`level=master` 为主 agent 阶段预留(本次仅实现 sub)

### Requirement: decide 流式展示思考阶段

系统 SHALL 将 `POST /api/tutoring/decide` 响应改为 SSE 流:先发射 agent 阶段事件(感知/解析/规划/决策),再发射 `meta` 事件携带 ActionMeta,最后 `done`。ActionMeta 内容与请求契约不变。

#### Scenario: decide 流式时序
- **WHEN** Java 调用 decide 且请求合法
- **THEN** 响应为 SSE,先 `agent(perceive/analyze/plan/decide)` 阶段事件,再 `meta`(data=ActionMeta),最后 `done`
- **THEN** ActionMeta 字段与流式改造前一致(闭集 type/eval/mastery_signals 等)

#### Scenario: 认证与校验不变
- **WHEN** decide 请求缺 token 或参数非法
- **THEN** 仍返回 403 / 422(与改造前一致,不因流式化改变错误语义)

### Requirement: generate 发射 agent 阶段事件

系统 SHALL 在 `POST /api/tutoring/generate` 的 SSE 流中发射 `agent(generate)` 阶段事件(配合已有 meta/token/done)。`memory` 阶段由 Java 在真实落库后发(Python 不发占位,避免双发)。

#### Scenario: generate 事件序列
- **WHEN** Java 调用 generate 且 action_type 合法
- **THEN** 流为先 `meta`(action_type),再 `agent(generate)`,再 `token*`,最后 `done`(不含 memory;memory 由 Java 落库后发)

#### Scenario: 类型先行
- **WHEN** generate 流开始
- **THEN** `meta`(action_type)在 `agent(generate)` 之前发出

### Requirement: Java 把关与记忆事件

Java 侧 SHALL 在护栏审批与掌握度落库的真实动作点,按协议发射 `agent(guardrail)` 与 `agent(memory)` 事件。

#### Scenario: 护栏把关可见
- **WHEN** Java 完成 decide 结果的护栏审批(reveal/轮次/安全/换题)
- **THEN** Java 发射 `agent(guardrail)`(status=done),透传给前端

#### Scenario: 记忆落库可见
- **WHEN** Java 完成 mastery_signals 落库(解析 kp_label→URI、更新掌握度、点亮图谱)
- **THEN** Java 发射 `agent(memory)`(status=done),透传给前端

### Requirement: thinking 事件(思考过程展示)

系统 SHALL 保留豆包思考模式,将模型真实推理 `reasoning_content` 作为附加内容流 `thinking` 事件流式透传,供前端展示"思考过程"。decide 与 generate 均须吐 thinking 事件;该事件对 Java 零改动(decide 过滤 meta 忽略,generate 直接透传)。

#### Scenario: decide 流式含 thinking
- **WHEN** Java 调用 decide 且走正常决策路径
- **THEN** 流中在 agent(analyze/plan) 之后、agent(decide) 之前发射 `event: thinking`(data 为推理分片,可多条)

#### Scenario: generate 流式含 thinking
- **WHEN** Java 调用 generate 且 action_type 合法
- **THEN** 流中在 agent(generate) 之后、token 之前发射 `event: thinking`(data 为推理分片,可多条)

#### Scenario: 短路分支不含 thinking
- **WHEN** decide 因 is_new_question 换题信号短路
- **THEN** 不发射 thinking 事件(未调用 LLM),只发 meta(type=switch)

### Requirement: 工具阶段协议预留

系统 SHALL 在事件协议中包含 `tool` 阶段,但本次不接入真实工具调用(知识图谱 agent 为将来独立的子 agent)。

#### Scenario: 协议含 tool 阶段
- **WHEN** 检查标准阶段表
- **THEN** 含 `tool` 阶段(预留),本次实现不发射真实 tool 事件

