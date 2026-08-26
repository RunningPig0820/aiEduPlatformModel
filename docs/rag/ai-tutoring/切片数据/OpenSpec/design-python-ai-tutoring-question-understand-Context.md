# design-python-ai-tutoring-question-understand

> summary: 说明Python辅导的多模态支持及现有代码事实情况
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Context
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring-question-understand
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-python-ai-tutoring-question-understand-Context.md
> 类别：项目介绍

---

## Context

- 题型分析前端需要图片入口；Java 通道 2（LlmGateway `/api/llm/chat`）纯文本。
- Python decide 已有看图能力（看图答疑，design 决策 14）：`ChatOpenAI(ark)` + `HumanMessage` image_url content blocks + doubao-seed-2-0-mini-260428（全模态），生产已验证。
- 现状代码事实：
  - `models/chat.py ChatRequest.message: str` —— 纯文本，无 image 字段，无结构化内容。
  - `/api/llm/chat` 被 page_assistant/faq/homework_grading/content_generation 等场景共用（生产共享网关）。
  - `config/model_config.py` 有 `supports_vision` 标记，但 zhipu glm-4.6v `allowed: False`（不对外）；doubao-seed-2-0-mini-260428 `allowed: True + supports_vision: True`。
