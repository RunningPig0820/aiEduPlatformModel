# 检索质量怎么评估？（hit@k/召回率/精确率）

> summary: 检索质量怎么评估？（hit@k/召回率/精确率）
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-67-数据关联-检索质量怎么评估hitk召回率精确率.md
> 类别：数据关联

---

## 回答

**核心结论**：hit@k（HIT_K=5）测"该捞的捞到没"=expected_references 命中召回 top-k 的比例、precision@k 测"捞上来的干不干净"=召回 top-k 中相关块占比，两指标互补分层定位；再加 LLM 判分（covered_count/fabricated 只报事实、分数硬算）与 quoted 引用校验、cost/latency。

**分层展开**：
- **hit@k**：`_match_file` 双向子串匹配（expected 引用与召回块 file 互含即命中），`hit_at_k` = expected_references 中命中召回 top-k 的比例（0~1，可多条引用部分命中）；k 默认 HIT_K=5（2026-08-26 由 3 改 5，对齐生成上下文 top-5）（依据：分析-06 eval_agent.py:58-83）。
- **precision@k**：召回 top-k 中相关块占比，分母=k；与 hit@k 互补——hit@k 看"该捞的捞到没"、precision@k 看"捞上来的干不干净"（依据：分析-06 eval_agent.py:89-105）。
- **分层定位**：先测检索（hit@k）再测答案（质量分），trace 回溯定位问题在哪一层——K2 首跑 hit@3=0.80 但质量 2.60，trace 发现是判分侧+评测集问题而非检索/生成（依据：坑档案 V2/K2）。
- **补充信号**：quoted 引用校验（lcs_quote_match 纯函数）+ cost/latency 三段耗时（retrieve/generate/total），报告里同时给"快不快/贵不贵"（依据：分析-06）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 67 问）｜ `3.代码/分析-06-评测.md`（hit_at_k/precision_at_k）｜ `4.完善文档/08-数据规模与指标.md` ｜ `5.难点/坑档案-开发与验证.md`（V2/K2）
