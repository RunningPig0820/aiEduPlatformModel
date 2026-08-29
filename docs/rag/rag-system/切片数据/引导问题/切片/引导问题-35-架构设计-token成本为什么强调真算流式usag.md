# token 成本为什么强调"真算"？流式 usage 只在结尾返回怎么拿？

> summary: token 成本为什么强调"真算"？流式 usage 只在结尾返回怎么拿？
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-35-架构设计-token成本为什么强调真算流式usag.md
> 类别：架构设计

---

## 回答

**核心结论**：成本是 RAG 最大实战痛点，真算+展示=成本控制叙事，估算只能标"估算"；流式 usage 只在流末尾专用 chunk 返回（OpenAI 兼容默认不返回），要显式带 `stream_options.include_usage` + 解析结尾 usage chunk（schema 与中间不同）。

**分层展开**：
- **为什么强调真算**：成本是 RAG 最大实战痛点，真算+展示 = 成本控制叙事；估算只能标"估算"，否则演示时露怯（依据：完善文档 03）。
- **流式 usage 只在结尾返回**：OpenAI 兼容流式**默认不返回 usage**，usage 只在流末尾"choices 为空但带顶层 usage"的专用 chunk 返回——schema 与中间 delta chunk 不同（依据：完善文档 03 / 坑档案 K6）。
- **怎么拿（修法）**：请求体显式带 `stream_options={"include_usage": true}`（`ark_stream.py:128-129`）+ `_parse_sse_lines` 识别流末尾 usage chunk 并 yield → `assemble_usage` 组装 prompt/completion/cache_hit/total → `done.tokens_usage`（依据：坑档案 K6 / 分析-07）。
- **半落地**：白盒流式 + 评测侧真采；1.6C `/query` 端点不采（generate 不带 return_usage、响应模型无 usage 字段）、embedding 未单列；cache_hit 取不到置 0 隐藏（0 不显示防误导）（依据：完善文档 08 / 分析-07）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 35 问）｜ `4.完善文档/03-为什么这么设计.md`、`08-数据规模与指标.md` ｜ `3.代码/分析-07-API降级与容错.md` ｜ `5.难点/坑档案-开发与验证.md`（K6）
