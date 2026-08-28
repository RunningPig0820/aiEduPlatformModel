# 答案生成与引用判定（doubao 流式生成 / is_quoted LCS 硬匹配）

> summary: 答案生成与引用判定 — doubao 流式生成 + is_quoted LCS 最长公共子串硬匹配（8 字窗口）
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-assistant-07-答案生成与引用判定.md
> 类别：操作流程


### 复用 vs 新增映射（generate 流式 / is_quoted）

> 检索摘要：答案生成与引用判定哪些复用现有代码、哪些是新增？

- **generate 流式**：`core/rag/generate`；复用 doubao 连接；新增改流式（复用 `ark_stream.stream_chat`）+ 8s 超时 + is_disconnected。
- **is_quoted**：新纯函数；新增 `lcs_quote_match(answer, block_texts) -> keys`。

### D-C. is_quoted（D6）

> 检索摘要：答案引用校验 is_quoted 怎么实现——LCS 最长公共子串硬匹配、8 字窗口、纯函数入评估？

- `lcs_quote_match(answer, blocks)`：对每个精排块的 text/summary，与 answer 做最长公共子串；`len(match) >= 8`（中文按字符）→ quoted。纯函数，入评估。
- done 后补发（chunk 粒度会撕裂连续 8 字窗口）。

### 白盒链路（generate / done 段）

> 检索摘要：白盒链路中答案生成与引用判定的事件产出——doubao 流式、is_disconnected 中止、done 带 quotedKeys？

```
 → generate(doubao 流式, 8s 超时→固定话术+召回清单)
     ←── is_disconnected → 中止流
 → done{answer, quotedKeys(LCS), tokensUsage, traceId, suggestions}
```

### Risks / Trade-offs（引用判定相关）

> 检索摘要：is_quoted 的 8 字窗口对 doubao 改写答案的风险——评估集加"改写答案"用例验证？

- [is_quoted 8 字窗口对改写答案] doubao 可能改写用词 → 评估集加"改写答案"用例验证窗口。
