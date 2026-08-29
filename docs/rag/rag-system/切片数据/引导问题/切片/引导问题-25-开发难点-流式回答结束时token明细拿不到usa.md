# 流式回答结束时 token 明细拿不到（usage 丢失），根因和修法是什么？

> summary: 流式回答结束时 token 明细拿不到（usage 丢失），根因和修法是什么？
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-25-开发难点-流式回答结束时token明细拿不到usa.md
> 类别：开发难点

---

## 回答

**核心结论**：K6：两层都丢——请求体没带 `include_usage`（服务端默认不回）+ 解析器不认结尾 usage chunk（choices 空带顶层 usage）；修法是 `ark_stream` 加 include_usage + 抓结尾 chunk 组装 `done.tokens_usage`。

**分层展开**：
- **现象**：SSE 流式回答结束后，前端成本面板拿不到本轮 token 明细（0 或空），"token 真算"变成摆设（依据：坑档案 K6）。
- **根因（两层都丢）**：①请求体无 `stream_options={"include_usage": true}`——OpenAI 兼容流式不加这个，服务端一般不会返回 usage；②`_parse_sse_lines` 只解析 reasoning/content/tool_calls，流末尾"choices 为空但带顶层 usage"的 chunk 被丢弃——两层都丢，"真算 + 流结束更新"无从落地（依据：坑档案 K6 / 完善文档 06）。
- **修法**：`ark_stream.py:128-129` 请求体加 `payload["stream_options"]={"include_usage": True}` + `_parse_sse_lines` 识别流末尾 usage chunk 并 yield；`stream_generate` 传 `include_usage=True`、`assemble_usage` 组装 prompt/completion/cache_hit/total → `done.tokens_usage`（依据：坑档案 K6 / 分析-07）。
- **半修（诚实口径）**：白盒流式已修；1.6C `/query` 端点仍丢（`generate` 不带 `return_usage`、`RAGQueryResponse` 无 usage 字段）、embedding 侧仍丢（`vector_store.embed()` 未抓 `resp.usage`）——面试表述按"白盒链路真采、1.6C/embedding 未接"为准（依据：坑档案 K6 / 分析-07）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 25 问）｜ `4.完善文档/06-关键坑与解法.md` ｜ `3.代码/分析-07-API降级与容错.md` ｜ `5.难点/坑档案-开发与验证.md`（K6）
