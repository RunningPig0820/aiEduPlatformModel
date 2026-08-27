# 题型名稳定规范

> summary: 题型名稳定规范：prompt 约束+few-shot 锚定常见题型，后端只字面归一化不做同义词聚类。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-ai-tutoring-topic-mastery-signal-D4-题型名稳定规范.md
> 类别：数据关联

---

### 决策 4：题型名稳定规范

> 检索摘要：题型名稳定规范：prompt 约束+few-shot 锚定常见题型，后端只字面归一化不做同义词聚类。

prompt 加约束：同一题型用**最常见、最短、规范的题型名**，不随意换说法；用 few-shot 锚定常见题型（鸡兔同笼/相遇问题/牛吃草）。理由：Java 只做字面归一化（全角半角/空白/去末尾语气词），不做同义词聚类，「鸡兔同笼」vs「鸡兔同笼问题」会被当两个题型 → 稳定性负担在 prompt 端。

> 证据：详见 `2.OpenSpec design 决策/design-python-ai-tutoring-topic-mastery-signal.md`（§决策 4）｜ 语雀-决策记录.md D26
