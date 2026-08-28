# token成本与真算

> summary: token成本与真算（design-python-project-intro-rag）：改ark_stream加include_usage解析结尾usage块流结束更新本轮、embedding抓usage.total_tokens单列、每轮+会话累计+¥换算成本展示
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-python-intro-rag-10-token成本与真算.md
> 类别：数据存储

---

### D7. token 真算(usage)+ 成本展示

> 检索摘要：token成本怎么真算并展示？改ark_stream请求加stream_options.include_usage解析结尾usage块，流结束更新本轮；embedding抓resp.usage.total_tokens单列，换算¥展示

- **改 `ark_stream.py`**:请求体加 `stream_options: {"include_usage": true}`,解析结尾 usage chunk(choices 空、顶层带 usage)→ 流结束更新本轮 prompt/completion。
- **改 `vector_store.py`**:`embed()` 抓 `resp.usage.total_tokens`,embedding tokens 单列。
- 展示:每轮 prompt/completion + 会话累计 + ¥ 换算(doubao 单价);embedding 单列。
- **为什么**:成本是 RAG 最大实战痛点;真算 + 展示 = 成本控制叙事。流式 usage 只在结尾返回 → "结束后更新"。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-python-project-intro-rag.md`（§D7. token 真算）
