# 风险与权衡（续）

> summary: 列举 analyze-question 链路运行风险（LLM 幻觉/阈值误并/冷启动波动/池过大等）与缓解手段，明细见正文。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-风险与权衡-2.md
> 类别：架构设计

---

### 风险与权衡（续）

> 检索摘要：列举 analyze-question 链路运行风险（LLM 幻觉/阈值误并/冷启动波动/池过大等）与缓解手段，明细见正文。

#### 风险清单（二）：冷启动与池约束风险

- [WEAK → PENDING 频率变高] → 冷启动猜测不再冒充 RESOLVED，PENDING 分支成常态路径；前端需覆盖「有 candidates」与「candidates 空」两种。
- [学段知识点池过大（数百）→ LLM 上下文超限] → 粗筛子池（题目关键词/题型名 name-LIKE）先缩容；子池空回退全池截断（MAX=200）；LLM 失败回退子池前 N 个（恒非空兜底）。
- [粗筛子池漏召回正确知识点] → 子池空/过小回退扩大召回（全池截断或去掉关键词过滤）；候选覆盖学段全池，仅排序由 LLM 决定。
- [掌握度层变体分裂未解] → 本期 Non-Goal；归一化已折叠硬变体，语义变体留大数据阶段。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§风险与权衡，下半）
