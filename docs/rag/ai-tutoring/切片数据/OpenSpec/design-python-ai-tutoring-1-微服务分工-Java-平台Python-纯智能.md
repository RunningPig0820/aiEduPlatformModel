# design-python-ai-tutoring

> summary: Java与Python在AI答疑中的微服务分工规则
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 1. 微服务分工:Java = 平台,Python = 纯智能
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-python-ai-tutoring-1-微服务分工-Java-平台Python-纯智能.md
> 类别：架构设计

---

### 1. 微服务分工:Java = 平台,Python = 纯智能

**选择**: Python 只做决策与生成,无状态;一切数据操作经 Java 域服务。护栏/会话/掌握度/错误事件/KG 解析/COS 归档归 Java。
**原因**: 业务数据(掌握度/会话)要被图谱叠加等 Java 侧功能消费,数据权威必须在 Java;Python 职责单一、可独立迭代。
**备选**: Python 持有会话与数据 —— 拒绝,破坏无状态边界,且与 Java 侧现有会话体系冲突。
