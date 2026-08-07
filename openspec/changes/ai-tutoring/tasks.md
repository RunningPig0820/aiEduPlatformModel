## 1. 前置:模型注册与冒烟测试

- [x] 1.1 `config/model_config.py` 注册 `deepseek-v4-flash`(deepseek 下,free=false, allowed=true)
- [x] 1.2 `config/settings.py` 新增 TUTORING_DECIDE_PROVIDER/MODEL、TUTORING_GENERATE_PROVIDER/MODEL、温度 env;`.env.example` 同步
- [x] 1.3 模型契约冒烟测试(spike): 用 deepseek-v4-flash 实测 function calling 是否支持,决定 structured.py 默认路径(走 function_calling 还是 json_mode)——**结论: function calling ✅ / json_mode ✅,默认走 function_calling(design 决策 5 已记录)**

## 2. 数据模型(models/tutoring.py)

- [x] 2.1 枚举:`ActionType`(hint/approach/reveal/concept/switch/end)、`EmotionF7`(七态)、`MasterySignal`(mastered/practicing/struggling)、`EndReason`(COMPLETED/ANSWER_REVEALED/ABANDONED/ROUND_LIMIT)
- [x] 2.2 `Eval`(correct/error_type/emotion/exercise_complete)、`MasterySignalItem`(kp_label/signal)
- [x] 2.3 `ActionMeta`(type/reason/eval/mastery_signals/new_question/end_reason/summary/safety_flag);`Eval` 与 `Decision` 独立子结构(可拆)
- [x] 2.4 `DecideRequest`(history/round_count/answer_request_count/mastery_snapshot/subject_hint)、`GenerateRequest`(history/subject_hint/action_type/action_meta)、`KpSnapshot`(无 current_question,当前题目由 Python 从 history 推断,见 design 决策 13)

## 3. 结构化输出保障(core/tutoring/structured.py)

- [x] 3.1 实现四段降级管线: bind_tools(ActionMeta)+手动解析 tool_call → JSON mode → 正则提取+Pydantic → 兜底 ActionMeta(type=hint)(实现发现: with_structured_output 走 json_schema 格式 deepseek 不支持,改 bind_tools,见 design 决策 5)
- [x] 3.2 schema 解析纠错重试(带 corrective prompt);重试域: 不重试 LLM 调用,只重试 schema 解析
- [x] 3.3 兜底与日志: 任何路径返回的 ActionMeta 都通过 Pydantic 校验;降级记日志

## 4. 提示词工厂(core/tutoring/prompts.py)

- [x] 4.1 decide 决策器系统提示词:闭集枚举+逐条语义、hint/approach 反例拆开、exercise_complete↔type=end 联动、从 history 推断当前题目(贴新题→switch)、终止型无关 vs 澄清型模糊区分、安全 flag、snapshot label 候选注入
- [x] 4.2 generate 分类型生成规约:hint 一条反问零步骤 / approach 思路大纲无最终数值 / reveal 完整解答 / concept 结合语境 / switch 确认换题 / end 按 end_reason 总结

## 5. 决策器与生成器(core/tutoring/)

- [x] 5.1 `context.py`: 历史截断(保留最近 ~12 条 + 当前题目恒在)、snapshot top-N、模型路由(decide/generate 按配置取模型)
- [x] 5.2 `decider.py`: 组装上下文 → 渲染 decide prompt → structured 调用 → ActionMeta
- [x] 5.3 `generator.py`: 按已放行 action_type 渲染生成规约 → llm.stream() → SSE token/done 事件(产出事件 dict: meta/token/done,SSE 格式化由 API 层做)

## 6. 端点层(api/tutoring.py + main.py)

- [x] 6.1 `POST /api/tutoring/decide`(非流式): 复用 verify_internal_token,返回 ActionMeta
- [x] 6.2 `POST /api/tutoring/generate`(流式 SSE): 复用 verify_internal_token,SSE token/done/error
- [x] 6.3 `main.py` 注册 tutoring 路由

## 7. OCR 前置(core/ocr_service.py)

- [x] 7.1 实现 `core/ocr_service.py`: recognize 返回 text/confidence(用百度 REST 接口非 baidu-aip,env 无 APP_ID,见 design 决策 11)
- [x] 7.2 `api/ocr.py` 补实现: 图片上传 → 识别题目文本;识别结果供前端确认/修改

## 8. 测试(tests/tutoring/)

- [x] 8.1 unit: ActionMeta schema 校验(闭集/必填/类型)、structured 降级管线逐段覆盖(mock 各段失败)
- [x] 8.2 unit: prompt 断言(每 action_type 生成规约存在、hint 禁数值、snapshot label 注入)
- [x] 8.3 unit: 边界用例——"我不会"→concept 不终止、"老师你好"→concept 澄清、"今天天气"→end、"英语题"→end、贴新题→switch、exercise_complete 联动 end
- [x] 8.4 integration(mock LLM): decide 返回合法 ActionMeta / 畸形降级兜底;generate 按类型约束流式;SSE 事件序列
- [x] 8.5 real(skip 无 key): deepseek-v4-flash 全流程——发起→引导→回答→换题→收尾→掌握度信号

## 9. 联调与收尾

- [ ] 9.1 与 Java 侧 ai-tutoring 联调: decide → Java 护栏 → generate 全链路(类型先行 SSE、护栏拒绝无 token)
- [x] 9.2 对齐 `docs/ai-tutoring-agent.md` 与契约(含 current_question 移除、从 history 推断;`reason` 字段是否纳入 Java 契约待 Java 侧确认)
- [ ] 9.3 确认 TUTORING_* 配置接入 Java 侧 ai-edu.tutoring 配置一致(模型地址/内部 token)

## 10. 豆包看图答疑(模型切 doubao + 图像优先,见 design 决策 14)

- [x] 10.1 **技术预演 spike**(先做,决定后面怎么走): 配置 DOUBAO + Factory 加 doubao provider;用真实题图(含公式/受力图)实测:
      ①图片+function calling 是否支持(①段 bind_tools 可用性) ②方舟能否直接访问 COS 签名 URL ③看图读题
      另确认: 加 image_url 后纯文本题目(无图)契约与行为是否不受影响(双通道向后兼容)
      结论决定: ①段走 tool calling 还是 json_mode;图片走 URL 还是 base64
      **结论(2026-08)**: ①③全过——图片+function calling ✅、COS URL 直接访问 ✅、看图读题公式全对 ✅;正确 ID=doubao-seed-2-0-lite-260428;①段走 tool calling、图片走 URL(design 决策 14 已记录)
- [x] 10.2 契约: `ChatTurn` 加 `image_url: Optional[str]`(文本与图片双通道;无图行为不变)
- [x] 10.3 `structured.py` 消息化: 四段降级改收消息列表;② JSON hint 改追加 SystemMessage;纠错重试带图设计(R12)——**真实题图 E2E 已验: doubao+图片+function calling → 合法 ActionMeta,并从图内公式识别出知识点**
- [x] 10.4 `prompts.py` 看图改造: 带图消息渲染 [图片题目] 占位 + 换题判定扩展(新图片消息→switch) + 看图决策指令
- [x] 10.5 `decider.py`/`generator.py` 多模态: 组装 SystemMessage + HumanMessage(文本 + image_url)——**真实 E2E 已验: decide 从图内识别知识点出 approach;generate(hint) 结合图引导不泄答案**
- [x] 10.6 测试回归(单元/集成)+ real 带图冒烟(doubao + 真实题图)——**2/2 通过: decide 读图识别知识点、generate 带图引导不泄答案;全量 115 passed**
- [ ] 10.7 可选(等 Java 删 OCR 端点后)删 `core/ocr_service.py` + `api/ocr.py` + 对应测试
