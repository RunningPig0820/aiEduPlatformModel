# design-python-ai-tutoring

> summary: 解决Java侧移除题目状态后Python推断当前题目的问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 13. Java 零题目状态:current_question 从契约移除(Java 侧定稿,2026-08)
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring
> 类别：开发难点

---

### 13. Java 零题目状态:current_question 从契约移除(Java 侧定稿,2026-08)

**选择**: decide/generate 请求**去掉 `current_question` 字段**。Java 不传、不记录、不维护题目内容(零题目状态);当前题目由 **Python 从 history 推断**,换题判定也在 Python。Java 只认 `type=switch` 重置计数,`new_question` 仅作展示可选、不落库。
**原因**: 题目内容属于对话上下文,不该由平台层双份维护;Java 拿它没有业务用途(审批只看 type+count),反而增加状态成本。
**实现**: 题目文本作为对话历史**首条 user 消息**进历史(OCR 结果 → 前端确认 → 首条 user 消息);decide prompt 增加"当前题目判定(关键)"规则(最新完整新题→switch、答题/追问→保持当前题、旧题只作参考、不被旧题带偏)。
**风险**: 换题判定从"后端权威"变为"LLM 推断",更依赖 prompt 质量。真实模型已验:求帮助→引导不 end、闲聊→end、贴新题→switch、hint 不泄答案(real 测试 4/4)。若实测换题误判率高,可给 decide 额外传轻量信号(如最新消息角色),但不回到后端维护题目。
