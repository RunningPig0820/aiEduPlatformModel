## Why

1. **等待黑盒**:AI 答疑每次 1-2 分钟才有答案,用户面对黑盒等待。要像豆包 agent 一样展示思考流程(感知→意图→规划→决策→生成→记忆),把"等待"变成"看到进展",大幅缓解等待感。
2. **答疑要成为可组合的"子 agent"**:最终愿景是"主 agent + 多领域子 agent"(答疑 / 知识图谱 / 错题集 / 批改)。答疑必须先做成**接口稳定、可插拔的子 agent**(稳定的契约 + 标准事件协议),将来主 agent 才能直接"选择它、调它、组合它"。
3. **Java 把关可见**:Java 的护栏审批(要答案/轮次/安全)与掌握度落库是真实且关键的动作,应作为 agent 流程的一环展示——这符合"Python = 决策智能、Java = 把关 + 流程控制 + 前端对接"的分工。

## What Changes

- **BREAKING**: decide 端点响应从"JSON 返回 ActionMeta"改为"SSE 流"——先发 agent 阶段事件(感知/解析/规划/决策),再发 `meta` 事件携带 ActionMeta,最后 `done`。请求不变,ActionMeta 内容不变。
- 新增 **agent 事件协议**:标准事件格式 `{level, stage, label, status, detail}` + 标准阶段表(perceive / analyze / plan / tool / decide / generate / memory / guardrail)。
- **thinking 事件(2026-08 追加)**: 保留豆包思考模式,把模型真实推理 `reasoning_content` 作为附加内容流 `event: thinking` 透传(decide + generate 都吐),黑盒等待变可见;Java 零改动。
- **generate 加 agent 阶段事件**:生成前发 `agent(generate)`(配合已有 meta/token/done 流);`agent(memory)` 由 Java 在真实落库后发(Python 不发占位,避免双发)。
- **Java 发把关/记忆事件**:护栏审批(`agent(guardrail)`)与掌握度落库(`agent(memory)`)由 Java 按协议发事件。
- **工具阶段(tool)协议预留、不实现真工具**:事件协议包含 `tool` 阶段与字段,但本次不接入真实工具(知识图谱 agent 是将来独立的子 agent,答疑届时通过工具调用它)。
- 事件协议支持**两层嵌套**(`level: master/sub`),为主 agent 编排预留(主 agent 的思考阶段 + 子 agent 的思考阶段可嵌套展示)。

## Capabilities

### New Capabilities
- `agent-flow-display`: agent 思考流程事件协议与展示——标准阶段事件、decide 流式阶段、generate 阶段、Java 把关/记忆阶段、两层嵌套预留。

### Modified Capabilities
<!-- 无全局 ai-tutoring capability,答疑契约改动并入本变更 scope -->

## Impact

- **ai-edu-ai-service**(Python):
  - `api/tutoring.py`: decide 改 SSE 流式响应
  - `core/tutoring/`: 事件发射(decider/generator)、阶段协议常量
  - `models/tutoring.py`: agent 事件模型(如需)
  - 测试: 事件序列测试
- **Java 侧**(aiEduPlatform 仓库):
  - decide 消费从"读 JSON"改"解析 SSE 流,提取 meta 事件"
  - 中继 agent 事件给前端
  - 发把关(guardrail)/记忆(memory)事件
- **前端**: 按协议渲染阶段进度(本次设计协议,渲染由前端侧配合)
- **契约**: decide 响应格式 breaking(Java 需一次性改造)
