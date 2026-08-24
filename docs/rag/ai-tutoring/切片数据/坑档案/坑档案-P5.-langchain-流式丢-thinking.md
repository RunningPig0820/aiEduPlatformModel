# 坑档案

> summary: 解决langchain流式返回丢失思考过程问题
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: P5. langchain 流式丢 thinking
> 模块: ai-tutoring ｜ 节: 坑档案

---

### P5. langchain 流式丢 thinking
- **坑**：流式想展示"思考过程"，但前端/Java 拿不到 reasoning。
- **根因**：langchain-openai 流式解析**丢弃 reasoning_content**（additional_kwargs 也为空）。
- **解决**：decide/generate 主路径改**直连方舟读原始 SSE**（`ark_stream.py`）；分层思考：decide 关思考（意图秒出）、generate 开思考（思考=AI 版进度条）。
- **证据**：`1cc9c88`、`efd35e2`；`ark_stream.py:1-15`。
