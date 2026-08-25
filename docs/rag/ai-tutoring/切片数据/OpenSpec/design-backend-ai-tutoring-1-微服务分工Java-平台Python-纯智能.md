# design-backend-ai-tutoring

> summary: 答疑AI后端Java与Python微服务分工规则
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 1. 微服务分工：Java = 平台，Python = 纯智能
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring

---

### 1. 微服务分工：Java = 平台，Python = 纯智能

**选择**: Java 持有认证、会话、护栏、掌握度、错误事件、KG 解析、COS 归档（数据与基础设施）；Python 答疑 agent（`ai-edu-ai-service` 现有 LLM 服务内的独立模块，不单独起服务）只做决策与生成，不直接访问任何数据源。

**原因**: 业务数据（掌握度/错误事件/会话）要被图谱叠加、错题本、学情等 Java 侧功能消费，数据权威必须在 Java；Python 作为独立智能微服务，职责单一、可独立迭代与扩容。
