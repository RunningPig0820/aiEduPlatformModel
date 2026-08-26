# 坑档案

> summary: 解决langchain流式返回丢失思考过程问题
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: P5. langchain 流式丢 thinking
> 模块: ai-tutoring ｜ 节: 坑档案
> COS路径: ai-tutoring/rag-slices/坑档案/坑档案-P5-langchain-流式丢-thinking.md
> 类别：开发难点

---

### P5. langchain 流式丢 thinking
**1. 问题现象**：流式想展示"思考过程"（decide 的推理 / generate 的推理），但前端/Java 拿不到 reasoning。

**2. 触发流程**：decide/generate 的流式主路径（`api/tutoring.py:41-81` decide、`:84-118` generate）→ `decider.py:115` / `generator.py:42` `streamer = ark_stream.stream_chat` → `core/tutoring/ark_stream.py:89-144` `stream_chat`（httpx.stream POST `{api_base}/chat/completions`）→ `_parse_sse_lines`（`:31-86`）逐行解析原始 SSE → yield `{"reasoning": delta.get("reasoning_content"), ...}`（`:81-86`）。decide 侧把 reasoning 吐成 thinking 事件（`decider.py:134-135`）；generate 侧 `enable_thinking=True` 流式展示推理。

**3. 根因分析**：langchain-openai 的 `ChatOpenAI` **流式解析会丢弃 `reasoning_content`**（实测 `additional_kwargs` 也为空）——不是模型不吐，而是 **SDK 解析层丢字段**。前端/Java 因此拿不到思考过程，reasoning 也无法用于流式决策。

**4. 排查过程**：前端说"没思考过程"→ Java 中继查 thinking 事件为空 → Python 打印流式 delta 发现 `reasoning_content` 存在但被 ChatOpenAI 丢弃 → 对比直连方舟原始 SSE 能拿到 → 定位为 SDK 解析层缺陷而非模型配置。

**5. 解决方案 & 改动点**：decide/generate 主路径改**直连方舟读原始 SSE**（`ark_stream.py`），请求体 thinking 开关参数化（`:126`）：`"thinking": {"type": "enabled" if enable_thinking else "disabled"}`。分层思考：decide 关思考（意图秒出 ~1.5s）、generate 开思考（`enable_thinking=True`，解答段思考 = AI 版进度条）。`generator.py:8-9`、`decider.py:134-135` 同步。测试 `tests/tutoring/unit/test_ark_stream.py`（`_parse_sse_lines` 纯函数）。

**6. 面试口述要点**：讲"**框架封装层丢字段，直连底层才拿到**"——langchain 流式丢 reasoning_content，是 SDK 兼容层缺陷。技术权衡：直连方舟读原始 SSE 换取字段完整性，但丢失框架的便捷性（自己拼消息、解析、错误处理）。踩坑收获：**流式字段依赖框架解析时，先验证框架是否真的透传**；分层思考（decide 关/generate 开）既是性能决策也是体验决策。

---
