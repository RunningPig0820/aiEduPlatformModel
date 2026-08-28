# 坑档案 K6 流式 token usage 丢失

> summary: 流式 token usage 默认不返回：请求显式 include_usage + 解析流末尾 usage chunk，done 事件携带 tokens_usage 修复成本展示
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: K6. 流式 token usage 丢失
> 模块: rag-system ｜ 节: 坑档案
> COS路径: rag-slices/rag-system/坑档案/坑档案-K6-流式usage丢失.md
> 类别：开发难点
> target: 开发对账

---

**1. 问题现象**：成本展示场景——RAG 助手 SSE 流式回答结束后，前端成本面板拿不到本轮 token 明细（0 或空），"token 真算"变成摆设，无法证明成本可观测。

**2. 触发流程**：提问 → 白盒链路 `stream_generate` → `ark_stream` 流式拉 doubao → 流结束 → `done` 事件 → 前端 CostBar。丢 usage 发生在 `ark_stream` 这一层：流式请求没带 `include_usage`，且流末尾"choices 为空但带顶层 usage"的 chunk 没被解析。

**3. 根因分析**：修前两层都丢——①请求体无 `stream_options={"include_usage": true}`（OpenAI 兼容流式不加这个，服务端一般不会返回 usage）→ 流里根本没有 usage；②`_parse_sse_lines` 只解析 `reasoning/content/tool_calls`，就算流里带 usage 也被丢弃。两层都丢，所以"真算 + 流结束更新"无从落地。

**4. 排查过程**：语雀-问题4 评审直接核流式代码定位（2026-08-24）：先查请求体有没有 `include_usage`（没有），再查解析器抓没抓结尾 usage chunk（没有）——是代码评审 + "OpenAI 兼容流式默认不返回 usage"的知识判断，不是线上日志。

**5. 解决方案 & 改动点**：白盒引擎 `62e9794` 落地两个小改动——`ark_stream.py:128-129` 请求体加 `payload["stream_options"] = {"include_usage": True}` + `_parse_sse_lines` 识别流末尾 usage chunk 并 yield；`assistant.py:448` `stream_generate` 传 `include_usage=True`、`476-477` 消费 usage delta、`486-502` `assemble_usage` 组装 prompt/completion/cache_hit/total → `done.tokens_usage`（`assistant.py:514/651`），前端 CostBar 展示四字段。⚠️ **半修**：1.6C `/query`（`api/rag.py:130` generate 不带 return_usage、`models/rag.py:39-44` 无 usage 字段）与 embedding（`vector_store.py:87-103` 未抓 resp.usage）仍未采——见附录 A2。

**6. 面试口述要点**：讲"流式输出的 usage 统计是 RAG 成本展示的隐性坑"——usage 只在流末尾的专用 chunk 返回、默认不带；要做"结束后更新"必须显式请求 `include_usage` 并解析结尾 chunk（choices 为空带顶层 usage，schema 与中间 delta 不同）。踩坑收获：流式协议层"你不主动要、服务端就不给"的默认值，以及"结尾 chunk 与中间 chunk 不同 schema"。

- **证据**：`62e9794`（白盒引擎 include_usage）+ `语雀-问题4`（"现有代码在丢 usage"）+ 附录 A2
