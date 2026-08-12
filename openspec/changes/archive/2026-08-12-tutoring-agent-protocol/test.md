# 答疑 agent 协议测试用例

## 测试数据

| 参数 | 值 | 说明 |
|-----|-----|------|
| EVENT_STAGES | perceive/analyze/plan/decide/generate/memory/guardrail | 标准阶段表 |
| TEST_IMAGE | https://ai-edu-1318177119.cos.../math.png | 看图用例 |

## 用例清单

### 1. agent 事件协议(unit)

| 用例 | 场景 | 预期 |
|------|------|------|
| EVT-001 | 阶段表齐全 | perceive/analyze/plan/tool/decide/generate/memory/guardrail 均在 |
| EVT-002 | 事件构造辅助 | `AgentEvent(stage=..., label=..., status=...)` 输出 `{level,stage,label,status,detail}` |
| EVT-003 | level 默认 sub | 构造的事件 level=sub;支持传 master(预留) |

### 2. decide 流式(integration, mock LLM)

| 用例 | 场景 | 预期 |
|------|------|------|
| DEC-001 | 正常决策流式 | SSE 序列: agent(perceive)→analyze→plan→decide → meta(ActionMeta) → done |
| DEC-002 | meta 内容不变 | meta 事件 data 的 type/eval/mastery_signals 与流式改造前一致 |
| DEC-003 | 换题信号短路 | is_new_question=true → 仍流式: agent 事件 + meta(type=switch) + done |
| DEC-004 | 缺 token | 403(流式前返回) |
| DEC-005 | 参数非法 | 422(流式前返回) |
| DEC-006 | 降级兜底 | 四段全失败 → 流式 agent 事件 + meta(type=hint, degraded=true) + done |

### 3. generate 阶段事件(integration, mock LLM)

| 用例 | 场景 | 预期 |
|------|------|------|
| GEN-001 | 正常流式 | meta → agent(generate) → token* → agent(memory) → done |
| GEN-002 | 空流兜底 | 零 token → token(固定引导话术) + done |
| GEN-003 | action_type 非法 | 422 |
| GEN-004 | 中段失败 | event: error,流终止 |

### 4. real(真实模型, skip 无 key)

| 用例 | 场景 | 预期 |
|------|------|------|
| REAL-001 | decide 流式全阶段 | 真实 doubao: 收到 agent(perceive→decide) + thinking* + meta(ActionMeta) + done |
| REAL-002 | generate 流式 | 真实 doubao: meta + agent(generate) + thinking* + token 流 + done(memory 由 Java 落库后发) |
| REAL-003 | 图片 decide 流式 | 图片题目: 流式阶段完整,meta 决策基于图 |

### 5. thinking 事件(unit/integration, mock streamer)

| 用例 | 场景 | 预期 |
|------|------|------|
| THK-001 | ark_stream SSE 解析 | `_parse_sse_lines` 从原始行提取 reasoning/content/tool_calls;[DONE] 结束;finish_reason=error 抛错 |
| THK-002 | decide 流式 thinking | iter_decide_events: reasoning 分片 → thinking 事件,在 meta 之前;meta 从 tool args 解析 |
| THK-003 | decide content 兜底 | 模型未走 tool_call 直接吐 ActionMeta JSON → 直接解析,不降级 |
| THK-004 | decide 短路 | is_new_question=true → 无 thinking,只 meta(type=switch) |
| THK-005 | decide 降级 | raw 流失败/args 非法 → 降级非流式 decide() → meta 仍合法 |
| THK-006 | generate thinking 穿插 | iter_tokens: meta → thinking* → token* → done;空流兜底只数 content |
| THK-007 | ChatTurn 附加字段 | history 带 thinking 字段 → 校验通过,字段被忽略(extra='ignore') |
| THK-008 | API 层 thinking 透传 | decide/generate SSE 含 `event: thinking`,时序正确(thinking 在 meta/token 前) |

### 6. 回归

- [ ] 既有 `ai-tutoring` 的单元/集成/real 全绿(decide 流式化不破坏 ActionMeta 契约)
- [ ] 错误语义(403/422)与改造前一致
- [ ] 138 tutoring 单元+集成全绿 + 9 real(含看图/完整流程)全绿

## 执行顺序

```
tests/tutoring/unit/test_agent_events.py     : 协议/构造
tests/tutoring/unit/test_ark_stream.py       : 原始 SSE 解析(reasoning/content/tool_calls)
tests/tutoring/unit/test_decider.py          : decide 流式 + thinking + 降级
tests/tutoring/unit/test_generator.py        : generate thinking/token 穿插
tests/tutoring/unit/test_models.py           : ChatTurn extra='ignore'
tests/tutoring/integration/test_tutoring_api.py : decide/generate SSE 含 thinking
tests/tutoring/real/test_agent_flow_real.py  : 真实模型
```
