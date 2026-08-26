# 想做流式展示"思考过程"，但 langchain 会把推理内容丢掉，你们怎么绕过去的？

> summary: 想做流式展示"思考过程"，但 langchain 会把推理内容丢掉，你们怎么绕过去的？
> 权威度: 1.0 ｜ 来源: 引导问题 ｜ 锚点: 想做流式展示"思考过程"，但 langchain 会把推理内容丢掉，你们怎么绕过去的？
> 模块: ai-tutoring ｜ 节: 开发难点
> COS路径: rag-slices/ai-tutoring/引导问题/引导问题-40-开发难点-想做流式展示思考过程但langcha.md
> 类别：开发难点

## 回答

**核心结论**：绕开 langchain，直连方舟读原始 SSE——langchain 流式解析会丢弃 reasoning_content。

**分层展开**：
- **现象**：流式想展示"思考过程"，但前端/Java 拿不到 reasoning（推理分片）。
- **根因**：langchain-openai 的 ChatOpenAI 流式解析**丢弃 reasoning_content**（实测 additional_kwargs 也为空）——想用现成封装展示思考，数据源就丢了。
- **解决**：decide/generate 主路径改为**直连方舟 OpenAI 兼容接口读原始 SSE**（ark_stream.py，httpx.stream），从流式 delta 里取 reasoning_content → thinking 事件逐字流入。
- **分层思考**：decide 关思考（意图秒出 1.2s），generate 开思考（长等待段思考 = AI 版进度条）——不是所有段都展示思考，只在长输出段用。
- **测试**：_parse_sse_lines 是纯函数，可离线单测（reasoning/content/tool_calls/usage 解析）。
- **追问点**："为什么不改 langchain 让它保留？" → 框架行为难以定制，直连更可控；直连也顺手拿到 function-calling 的 tool args 流式累积。
