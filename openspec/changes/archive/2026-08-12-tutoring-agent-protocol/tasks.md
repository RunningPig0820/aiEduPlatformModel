## 1. 事件协议定义

- [x] 1.1 `core/tutoring/agent_events.py`(新): 定义 agent 事件常量——标准阶段表(perceive/analyze/plan/tool/decide/generate/memory/guardrail)、`AgentEvent` 构造辅助、`level`(sub/master)、`status`(processing/done/error)
- [x] 1.2 事件格式与 api.md 对齐:`{level, stage, label, status, detail}`;label 用中文展示文案(如 "读取题目"/"解析意图"/"规划引导"/"决策"/"生成中"/"记忆更新"/"安全把关")

## 2. decide 流式化(展示思考阶段)

- [x] 2.1 `api/tutoring.py` decide 改 SSE 流式: 先 `agent(perceive)` → `agent(analyze)` → `agent(plan)` → `agent(decide)` → `meta(data=ActionMeta)` → `done`(response_model 移除,改 StreamingResponse)
- [x] 2.2 短路分支(换题信号 is_new_question / 降级兜底)也走流式: 发相应阶段事件 + `meta(ActionMeta)` + `done`
- [x] 2.3 错误语义保持: 403(缺 token)/ 422(参数校验)在流式前返回,与改造前一致

## 3. generate 加 agent 阶段事件

- [x] 3.1 `api/tutoring.py` generate: 流中加 `agent(generate)`(生成前)、`agent(memory)`(done 前)
- [x] 3.2 空流兜底保留(零 token → 固定引导话术)

## 4. Java 侧对接(跨仓库,Python 侧给契约 + 联调)

- [x] 4.1 同步 decide 流式契约给 Java: Java 从"读 JSON"改"解析 SSE 流,提取 meta 事件"(已交付 `docs/ai-tutoring-agent-events.md`,含 TutoringLlmClient 改法示例)
- [x] 4.2 Java 中继 Python 的 agent 事件 + 发 `agent(guardrail)` / `agent(memory)`(契约已交付;Java 实现待 Java 侧按文档执行)
- [x] 4.3 确认 guardrail/memory 事件的触发点与文案(2026-08 后端联调定案: memory=Java 发/Python 删占位;guardrail 触发点=护栏通过后;decide 流式后重试=首事件前可重试;错误=error 事件透传不重试——见 design 决策 7 / docs/ai-tutoring-agent-events.md)

## 5. 测试

- [x] 5.1 unit: `agent_events.py` 阶段表/构造辅助;decide 流式的事件序列(FakeLLM mock)
- [x] 5.2 integration: decide SSE 事件序列(meta 携带 ActionMeta、done 收尾);generate 含 agent(generate)/agent(memory)
- [x] 5.3 real: 真实模型 decide 流式 + generate 流式的事件完整覆盖(2/2 通过)
- [x] 5.4 回归: 原有单元/集成/real 全绿(contract 变化不破坏既有行为)——**全量 129 passed**

## 6. 文档

- [x] 6.1 `api.md`: decide 响应改 SSE 流式 + agent 事件协议 + 事件时序(本变更 api.md 已有;`ai-tutoring/api.md` 已标注演进)
- [x] 6.2 `design.md`: 事件协议、阶段表、Java 把关/记忆事件、工具阶段预留、两层嵌套(本变更 design.md 已有;`ai-tutoring/design.md` 决策 2 + `docs/ai-tutoring-agent.md` 3.1 已同步)
- [x] 6.3 本变更(proposal/specs)与 `ai-tutoring` 变更的契约衔接确认(design.md 新增衔接段: ActionMeta/请求契约不变,BREAKING 仅 decide 响应载体)

## 7. thinking 事件(2026-08 追加: 保留豆包思考模式,流式展示推理过程)

- [x] 7.1 spike 验证: 豆包 `reasoning_content` 流式可达;langchain-openai 流式**丢弃** reasoning(additional_kwargs 为空)→ 必须直连方舟读原始 SSE;thinking + tools(function calling)并存(R1-R3)
- [x] 7.2 `core/tutoring/ark_stream.py`(新): 原始方舟 SSE 客户端——`stream_chat`(httpx + `thinking: enabled`)/`_parse_sse_lines`(纯函数)/`messages_to_openai`(多模态透传)/`action_meta_tool`(ActionMeta JSON Schema)/`doubao_conn`(与 LLMFactory 单一来源)
- [x] 7.3 `decider.iter_decide_events()`(新): 流式决策——reasoning→thinking 事件;tool_calls 累积→ActionMeta;模型未走 tool_call 直接吐 ActionMeta JSON→解析(content 兜底);失败降级现有非流式四段管线
- [x] 7.4 `generator.iter_tokens()` 改造: `llm.stream()` → 原始方舟流式,吐 thinking + token;空流兜底只数 content
- [x] 7.5 `api/tutoring.py`: decide 端点接 `iter_decide_events`,thinking 事件透传;generate 流式零改动(else 分支转发)
- [x] 7.6 `ChatTurn` 显式 `extra='ignore'`(Java 在历史消息附加 thinking 字段,仅存储/展示用;固化容忍附加字段契约,防未来严格模式)
- [x] 7.7 测试: 单元(ark_stream 解析 / iter_decide_events thinking+降级 / iter_tokens thinking 穿插 / ChatTurn 附加字段)+ 集成(monkeypatch `ark_stream.stream_chat`,断言 thinking 时序)+ real(豆包看图/完整流程 9 用例通过)
- [x] 7.8 文档: api.md(thinking 事件)、design.md(决策 8/9)、spec.md(thinking 需求)、docs/ai-tutoring-agent-events.md(第〇节,Java 零改动说明)
