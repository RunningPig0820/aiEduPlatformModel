# ActionMeta作为跨语言契约，Java与Python两边版本迭代，如何避免契约不兼容引发线上故障？

> summary: 单一来源 + 平铺契约 + 容忍附加字段 + 集成测试，四道防线避免契约不兼容引发线上故障。
> 权威度: 1.0 ｜ 来源: 引导问题 ｜ 锚点: ActionMeta作为跨语言契约，Java与Python两边版本迭代，如何避免契约不兼容引发线上故障？
> 模块: ai-tutoring ｜ 节: 架构权衡
> 类别：架构设计

## 回答

**核心结论**：单一来源 + 平铺契约 + 容忍附加字段 + 集成测试，四道防线避免契约不兼容引发线上故障。

**分层展开**：
- **单一来源**：Python 侧 Pydantic 模型（models/tutoring.py）即 schema（同时绑定给 LLM 做 function calling），Java 侧对齐 api.md——两边从同一份契约开发，不各自发明。
- **兼容设计**：平铺契约 + 闭集枚举；ChatTurn extra='ignore' 容忍 Java 附加字段（如 thinking）——不因多余字段校验失败。
- **版本迭代纪律**：字段只增不删、向后兼容；新增字段 Java 侧先升级消费方；改字段名走全链路同步（曾踩坑：J3 序列化字段名不匹配 kp_label vs topic_label → 每轮"网络波动"，全网改 topic_label）。
- **集成测试**：真实请求链路（Java 集成测试 → Python 端点）在发布前跑通，契约断裂在测试层暴露，不等到线上。
- **追问点**："Python 改了契约怎么通知 Java？" → 契约文件（api.md/models.py）同步更新 + 集成测试 + 发布 checklist；字段只增不删，新增不破坏旧调用。
