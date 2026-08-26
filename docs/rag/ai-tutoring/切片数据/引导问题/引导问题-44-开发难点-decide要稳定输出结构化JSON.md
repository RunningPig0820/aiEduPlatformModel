# decide 要稳定输出结构化 JSON，模型不给力时你们做了哪些兜底？

> summary: 四段降级管线 + 纠错重试，保证绝不吐畸形、绝不抛异常——结构化输出的工程化兜底。
> 权威度: 1.0 ｜ 来源: 引导问题 ｜ 锚点: decide 要稳定输出结构化 JSON，模型不给力时你们做了哪些兜底？
> 模块: ai-tutoring ｜ 节: 开发难点
> COS路径: rag-slices/ai-tutoring/引导问题/引导问题-44-开发难点-decide要稳定输出结构化JSON.md
> 类别：开发难点

## 回答

**核心结论**：四段降级管线 + 纠错重试，保证绝不吐畸形、绝不抛异常——结构化输出的工程化兜底。

**分层展开**：
- **四段降级**：① bind_tools(function calling)——ActionMeta 作为 function tool，args 交 Pydantic 校验；② JSON mode——response_format=json_object + 解析校验；③ 正则提取 + Pydantic——容忍混杂文本；④ 兜底 type=hint + degraded=true。
- **纠错重试**：每段内 schema 纠错（只修 JSON 不整段重生成，重试域有上限），多模态场景纠错消息追加保持图片上下文。
- **为什么不用 with_structured_output**：langchain-openai 1.x 默认走 response_format=json_schema（Structured Outputs），deepseek 不支持（400）；bind_tools 走原生 tool-calling，实测可用。
- **emotion 归一化**：模型把情绪填成"困惑/confused"中文小写 → 映射到大写枚举，避免整条 ActionMeta 校验失败丢 mastery_signals。
- **degraded 标志**：兜底返回 type=hint + degraded=true，Java 监控 Python 降级频次，不用 503 阻断。
- **追问点**："四段都失败会怎样？" → 返回 type=hint 温和提示，绝不泄答案、绝不阻塞——宁可降级也不让会话卡死。
