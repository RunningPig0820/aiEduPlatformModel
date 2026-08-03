## 1. 前置:模型注册与冒烟测试

- [ ] 1.1 `config/model_config.py` 注册 `deepseek-v4-flash`(deepseek 下,free=true, allowed=true)
- [ ] 1.2 `config/settings.py` 新增 TUTORING_DECIDE_PROVIDER/MODEL、TUTORING_GENERATE_PROVIDER/MODEL、温度 env;`.env.example` 同步
- [ ] 1.3 模型契约冒烟测试(spike): 用 deepseek-v4-flash 实测 function calling 是否支持,决定 structured.py 默认路径(走 function_calling 还是 json_mode)

## 2. 数据模型(models/tutoring.py)

- [ ] 2.1 枚举:`ActionType`(hint/approach/reveal/concept/switch/end)、`EmotionF7`(七态)、`MasterySignal`(mastered/practicing/struggling)、`EndReason`(COMPLETED/ANSWER_REVEALED/ABANDONED/ROUND_LIMIT)
- [ ] 2.2 `Eval`(correct/error_type/emotion/exercise_complete)、`MasterySignalItem`(kp_label/signal)
- [ ] 2.3 `ActionMeta`(type/reason/eval/mastery_signals/new_question/end_reason/summary/safety_flag);`Eval` 与 `Decision` 独立子结构(可拆)
- [ ] 2.4 `DecideRequest`(history/round_count/answer_request_count/current_question/mastery_snapshot/subject_hint)、`GenerateRequest`(history/current_question/subject_hint/action_type/action_meta)、`KpSnapshot`

## 3. 结构化输出保障(core/tutoring/structured.py)

- [ ] 3.1 实现四段降级管线: with_structured_output(function_calling) → JSON mode → 正则提取+Pydantic → 兜底 ActionMeta(type=hint)
- [ ] 3.2 schema 解析纠错重试(带 corrective prompt);重试域: 不重试 LLM 调用,只重试 schema 解析
- [ ] 3.3 兜底与日志: 任何路径返回的 ActionMeta 都通过 Pydantic 校验;降级记日志

## 4. 提示词工厂(core/tutoring/prompts.py)

- [ ] 4.1 decide 决策器系统提示词:闭集枚举+逐条语义、hint/approach 反例拆开、exercise_complete↔type=end 联动、current_question 权威、终止型无关 vs 澄清型模糊区分、安全 flag、snapshot label 候选注入
- [ ] 4.2 generate 分类型生成规约:hint 一条反问零步骤 / approach 思路大纲无最终数值 / reveal 完整解答 / concept 结合语境 / switch 确认换题 / end 按 end_reason 总结

## 5. 决策器与生成器(core/tutoring/)

- [ ] 5.1 `context.py`: 历史截断(保留最近 ~12 条 + 当前题目恒在)、snapshot top-N、模型路由(decide/generate 按配置取模型)
- [ ] 5.2 `decider.py`: 组装上下文 → 渲染 decide prompt → structured 调用 → ActionMeta
- [ ] 5.3 `generator.py`: 按已放行 action_type 渲染生成规约 → llm.stream() → SSE token/done 事件

## 6. 端点层(api/tutoring.py + main.py)

- [ ] 6.1 `POST /api/tutoring/decide`(非流式): 复用 verify_internal_token,返回 ActionMeta
- [ ] 6.2 `POST /api/tutoring/generate`(流式 SSE): 复用 verify_internal_token,SSE token/done/error
- [ ] 6.3 `main.py` 注册 tutoring 路由

## 7. OCR 前置(core/ocr_service.py)

- [ ] 7.1 实现 `core/ocr_service.py`(复用 baidu-aip): recognize 返回 text/confidence
- [ ] 7.2 `api/ocr.py` 补实现: 图片上传 → 识别题目文本;识别结果供前端确认/修改

## 8. 测试(tests/tutoring/)

- [ ] 8.1 unit: ActionMeta schema 校验(闭集/必填/类型)、structured 降级管线逐段覆盖(mock 各段失败)
- [ ] 8.2 unit: prompt 断言(每 action_type 生成规约存在、hint 禁数值、snapshot label 注入)
- [ ] 8.3 unit: 边界用例——"我不会"→concept 不终止、"老师你好"→concept 澄清、"今天天气"→end、"英语题"→end、贴新题→switch、exercise_complete 联动 end
- [ ] 8.4 integration(mock LLM): decide 返回合法 ActionMeta / 畸形降级兜底;generate 按类型约束流式;SSE 事件序列
- [ ] 8.5 real(skip 无 key): deepseek-v4-flash 全流程——发起→引导→回答→换题→收尾→掌握度信号

## 9. 联调与收尾

- [ ] 9.1 与 Java 侧 ai-tutoring 联调: decide → Java 护栏 → generate 全链路(类型先行 SSE、护栏拒绝无 token)
- [ ] 9.2 对齐 `docs/ai-tutoring-agent.md` 与契约(含 `reason` 字段是否纳入 Java 契约的确认)
- [ ] 9.3 确认 TUTORING_* 配置接入 Java 侧 ai-edu.tutoring 配置一致(模型地址/内部 token)
