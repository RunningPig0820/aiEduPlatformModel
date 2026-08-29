# 评测体系（指标定义 / 判分模型 / 可观测性）

> summary: 评测体系 — 四指标定义 + doubao 判分模型 + trace/报告可观测性
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-eval-agent-12-评测体系-2.md
> 类别：数据关联


### D4. 指标定义

> 检索摘要：评测四指标：hit@k 取 k=3 按预期引用命中召回 top-k 比例算、answer_quality 按准确性/引用正确性/覆盖要点判0~5分、cost 按 tokens×单价、latency 分检索/生成/总耗时。

- `hit@k`：预期引用（page+section）中，出现在召回 top-k 的比例。k 取 3（源文档池 top-k）。
- `answer_quality`：LLM 判分 0~5，按 准确性/引用正确性/覆盖要点 三方面。
- `cost`：累计 prompt+completion tokens × 单价（doubao），复用 rag-generation 的 usage 真算。
- `latency`：检索耗时、生成耗时、总耗时（超时按降级计）。
- **为什么**：这 4 个指标分别回答"捞得对不对、答得好不好、贵不贵、快不快"。

> 代码演进注：设计稿 k=3，真实实现代码已演进为 HIT_K=5（以代码为准）。

### D5. 判分模型：doubao（复用 ark_stream）

> 检索摘要：判分模型选 doubao 复用 ark_stream，判分 prompt 输入答案+预期要点+预期引用输出严格 JSON {score, rationale}，与生成同模型能力一致，本地小模型与人工判分被弃。

- 判分 prompt：给 答案 + 预期要点 + 预期引用 → 输出 `{score, rationale}`（严格 JSON）。
- **为什么**：与生成同模型，能力一致；复用现成 doubao + usage 链路。
- **备选**：本地小模型判分 → 与生成模型能力不一致，弃；人工判分 → 不可扩展，弃。

> 代码演进注：设计稿为 LLM 判分，真实实现代码已演进为判分改硬算（编造封顶 3，以代码为准）。

### D6. 可观测性：trace + 报告

> 检索摘要：可观测性靠每轮 trace（JSONL）记录 query/召回/得分/引用/usage/耗时/判分与按模块及全量聚合的报告，支持不同语料版本对比，用数据证明 RAG 有效。

- 每轮评测落 trace（JSONL）：query、检索池、召回条目+得分、是否命中、生成答案、引用、usage、耗时、判分。
- 报告：按模块聚合 + 全量聚合；支持对比"不同语料版本"（重新评测后对比 hit@k/质量分变化）。
- **为什么**：面试要"用数据证明有效"——报告就是证据；trace 让问题可定位到具体一条评测。
- **备选**：只输出汇总数字 → 说不清"哪条不行、为什么不行"，弃。
