# WEAK 幻觉排除聚合
> summary: 冷启动 LLM 猜测标记 WEAK，聚合 findResolved 排除 WEAK 防幻觉进题型库；analyze 对 WEAK 降级为候选待确认而非权威。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-边界场景清单-场景24-WEAK幻觉排除聚合.md
> 类别：数据关联
> 状态：✅
> entry_id: 场景24
> source_doc: 语雀-边界场景清单.md
> tags: ["场景24","掌握度底盘&题型分析","status_done"]

---

### 场景24：WEAK 幻觉排除聚合（LLM 幻觉不进题型库）
> 状态：✅
> 检索摘要：冷启动 LLM 猜测标记 WEAK，聚合 findResolved 排除 WEAK 防幻觉进题型库；analyze 对 WEAK 降级为候选待确认而非权威。

| 属性 | 内容 |
|---|---|
| 业务场景 | WEAK 幻觉关联 |
| 触发条件 | LLM 冷启动消歧幻觉（如「对数方程求解」被关联到错误题型/知识点） |
| 当前处理 | KpResolution.weak 标记；聚合 findResolved/findResolvedByTopicLabels 排除 WEAK；analyze 对 WEAK 降级候选待确认 |
| 兜底降级策略 | WEAK 需第二信号（共现/维护重判）转正才入题型库 |
| 残余风险 | 冷启动 WEAK→PENDING 频率变高，前端需覆盖有/无候选两种 |
| 证据 | design-backend-kp-question-analysis D7 |

> 证据：详见 `1.语雀/语雀-边界场景清单.md`（§场景24）｜ 完善文档 06-题型动态聚集与向量.md ｜ OpenSpec design-backend-kp-question-analysis D7（历史设计文档，请核对代码确认实际落地）
