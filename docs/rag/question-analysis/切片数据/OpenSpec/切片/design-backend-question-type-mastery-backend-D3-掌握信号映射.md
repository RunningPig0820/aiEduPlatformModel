# 掌握信号映射

> summary: 掌握信号映射：直接答对/求助后答对/答错分级打分，per-题型前几题打折，Java 从引导量推断 Python 零改动。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-question-type-mastery-backend-D3-掌握信号映射.md
> 类别：数据存储

---

### Decision 3：掌握信号映射——直接答对/引导后答对/答错，Python 零改动

> 检索摘要：掌握信号映射：直接答对/求助后答对/答错分级打分，per-题型前几题打折，Java 从引导量推断 Python 零改动。

```
直接答对（answer_request_count=0，学生未主动求助）→ score = 1.0
求助后答对（answer_request_count≥1，学生要过思路/答案）→ score = 0.5
答错 / 未完成                                   → score = 0.0
× per-题型前几题打折（第1题70% / 第2题80% / 第3题起100%，可配置）
```

- **复用现有资产**：会话实体已有 `roundCount`（引导轮数）、`answerRequestCount`（要答案次数），Java 侧直接取，**Python 不新增字段**。
- **为什么用引导量而非 hinted 布尔**：连续引导量（hint_count/answer_request_count）比布尔更细，将来可 `0.6^hint_count` 衰减；且不触 Python 契约。
- **打分 scoping = per 题型**（对每个题型，它的第 1 题打折）——学习新题型都是从不会开始；与现状 per-题型 max 天然一致。

> 证据：详见 `2.OpenSpec design 决策/design-backend-question-type-mastery-backend.md`（§Decision 3）｜ 语雀-决策记录.md D4 ｜ 完善文档 05-数据落库与掌握度.md
