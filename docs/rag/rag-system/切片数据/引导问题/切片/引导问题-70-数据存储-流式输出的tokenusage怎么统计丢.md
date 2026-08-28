# 流式输出的 token usage 怎么统计？（丢 usage 坑）

> summary: 流式输出的 token usage 怎么统计？（丢 usage 坑）
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-70-数据存储-流式输出的tokenusage怎么统计丢.md
> 类别：数据存储

---

## 回答

**核心结论**：流式 usage 只在流末尾专用 chunk 返回（choices 为空带顶层 usage）且默认不带——必须请求体加 stream_options.include_usage + 解析结尾 usage chunk（schema 与中间 delta 不同）；白盒链路已修，1.6C/embedding 侧仍丢（半修）。

**分层展开**：
- **坑根因（K6）**：两层都丢——请求体没带 `include_usage`（OpenAI 兼容流式默认不返回 usage）+ 解析器不认结尾 usage chunk（choices 空带顶层 usage 被丢弃），所以"真算+流结束更新"无从落地（依据：坑档案 K6）。
- **修法**：`ark_stream.py:128-129` 请求体加 `stream_options={"include_usage": True}` + `_parse_sse_lines` 识别流末尾 usage chunk 并 yield；`assistant.py` `stream_generate` 传 include_usage=True、`assemble_usage` 组装 prompt/completion/cache_hit/total 进 `done.tokens_usage`，前端 CostBar 展示四字段（依据：坑档案 K6 / 分析-04）。
- **⚠️ 半修现状**：白盒流式已修 + 评测线已抓（`generate(return_usage=True)` 读 usage_metadata）；但 **1.6C /query 仍丢**（generate 不带 return_usage、RAGQueryResponse 无 usage 字段）、**embedding 侧仍丢**（`vector_store.embed()` 不抓 resp.usage.total_tokens）——面试讲"token 真算"要分清哪条线真采（依据：分析-07 对账要点 / 坑档案 A2）。
- **面试口述要点**：踩坑收获是"流式协议层你不主动要、服务端就不给"，以及"结尾 chunk 与中间 chunk 不同 schema"（依据：坑档案 K6）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 70 问）｜ `5.难点/坑档案-开发与验证.md`（K6/A2）｜ `3.代码/分析-04-检索编排.md`、`分析-07-API降级与容错.md`（ark_stream.py:128-129）
