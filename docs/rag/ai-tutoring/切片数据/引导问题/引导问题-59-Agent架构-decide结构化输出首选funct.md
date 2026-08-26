# decide 结构化输出首选 function calling，为什么不直接用 with_structured_output？

> summary: with_structured_output 的默认实现（Structured Outputs）不兼容 deepseek，bind_tools 走原生 tool-calling 更稳。
> 权威度: 1.0 ｜ 来源: 引导问题 ｜ 锚点: decide 结构化输出首选 function calling，为什么不直接用 with_structured_output？
> 模块: ai-tutoring ｜ 节: Agent架构
> COS路径: rag-slices/ai-tutoring/引导问题/引导问题-59-Agent架构-decide结构化输出首选funct.md
> 类别：架构设计

## 回答

**核心结论**：with_structured_output 的默认实现（Structured Outputs）不兼容 deepseek，bind_tools 走原生 tool-calling 更稳。

**分层展开**：
- **不直接用 with_structured_output**：langchain-openai 1.x 默认走 response_format=json_schema（Structured Outputs），deepseek 不支持会报 400；bind_tools 走原生 tool-calling，实测可用。
- **bind_tools 方案**：ActionMeta（Pydantic 模型）直接作为 function tool 绑定，参数 JSON Schema 直传方舟（含 $defs，实测 200 + 完整 tool args + Pydantic 校验通过）；args 交 Pydantic 严格校验。
- **兜底**：模型未走 tool_call、直接把 ActionMeta JSON 当 content 返回（关思考后 mini 偶发）→ 从 content 提取解析（_extract_json），避免 reason/mastery_signals 丢失。
- **再兜底**：四段降级管线——function calling → JSON mode → 正则提取 → type=hint；段内 schema 纠错重试。
- **追问点**："为什么 deepseek 不支持？" → langchain-openai 的 Structured Outputs 依赖特定 response_format，deepseek 兼容层不实现 json_schema——bind_tools 是兼容性最好的原生路径。
