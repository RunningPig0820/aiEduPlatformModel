# design-python-ai-tutoring

> summary: Python AI答疑agent的上下文与现有地基说明
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Context
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-ai-tutoring-Context.md
> 类别：项目介绍

---

## Context

学生端"AI 答疑"是产品核心体验:拍照传题 → OCR → 引导式解答(先引导、后答案)→ 分析薄弱知识点 → 图谱点亮。本变更是 Python 侧答疑 agent 实现,对应 Java 仓库 `openspec/changes/ai-tutoring/`(护栏/会话/掌握度/落库/COS 归档由 Java 承担)。

关键架构认识:**对话天然是 agent 形态**,学生不会按预设流程走。**不做流程状态机控制对话**(状态会爆炸),改为**能力受限 agent + 工具护栏**:Python 纯智能(决策+生成)、无状态、不碰 MySQL/KG/COS;Java 平台(认证/护栏/数据/编排)。Java 在动作出口做硬护栏——审批归属 Java 不是 Python(数据在 Java、球员不能当裁判、防提示词攻击、规则数字可页面/配置运营控制)。

现有地基:`ai-edu-ai-service` FastAPI 服务,已有 `verify_internal_token` 内部认证、`core/gateway/` LLM 工厂、`api/chat.py` 的 SSE 流式骨架(chat/stream)、`requirements.txt` 已装 baidu-aip OCR 依赖(模块是 stub)。参考: `docs/ai-tutoring-agent.md`(本仓库已沉淀的 Python agent 设计)。
