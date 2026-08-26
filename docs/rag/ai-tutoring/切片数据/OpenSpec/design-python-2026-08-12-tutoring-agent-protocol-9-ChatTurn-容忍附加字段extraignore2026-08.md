# design-python-2026-08-12-tutoring-agent-protocol

> summary: 设置 ChatTurn 容忍附加字段的契约规则
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 9. ChatTurn 容忍附加字段(extra='ignore',2026-08)
> 模块: ai-tutoring ｜ 节: design-python-2026-08-12-tutoring-agent-protocol
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-python-2026-08-12-tutoring-agent-protocol-9-ChatTurn-容忍附加字段extraignore2026-08.md
> 类别：架构设计

---

### 9. ChatTurn 容忍附加字段(extra='ignore',2026-08)

Java 在历史消息上附加 `thinking` 字段(仅 Java 存储/前端展示用),会出现在 decide/generate 请求里。
`ChatTurn` 显式 `model_config = ConfigDict(extra="ignore")`,固化"容忍附加字段"契约:

- 该字段在 Pydantic 校验时被剥离,**不进请求模型**
- 提示词渲染(`_format_history`)只读 role/content/image_url → **thinking 永不进 LLM prompt**(避免模型看到自己旧推理偏置)
- 显式声明防未来误开 `extra='forbid'` 严格模式导致校验失败
- 回归测试: `test_models.py`(ChatTurn 附加字段 + 请求级 history 带 thinking 校验通过)
