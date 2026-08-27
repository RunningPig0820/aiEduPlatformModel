# 契约变更

> summary: getMastery 契约 BREAKING：masteryLevel 四档改连续百分比，新增 source/trainCount，前端分桶保留四档视觉。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-question-type-mastery-D8-契约变更.md
> 类别：开发难点

---

### 决策 8：`getMastery` 契约变更（BREAKING，需联调）

> 检索摘要：getMastery 契约 BREAKING：masteryLevel 四档改连续百分比，新增 source/trainCount，前端分桶保留四档视觉。

现有 `getMastery` 返回离散四档 `{0,25,50,75}` + status。本期改为**连续百分比** + 来源 + 训练数：

```js
// 请求不变：GET /students/{id}/mastery
// 响应 items[].masteryLevel 语义变更：0-100 连续百分比（原 0/25/50/75）
// 新增字段：source('ai'|'bank')、trainCount、topicLabel
```

**前端分桶展示**：连续百分比 → 徽标（如 <25 待巩固 / 25-50 练习中 / 50-75 / ≥75 已掌握），保留现有四档视觉。**知识点总览页不再消费本接口做覆盖度。**

> 证据：详见 `2.OpenSpec design 决策/design-frontend-question-type-mastery.md`（§决策 8：`getMastery` 契约变更（BREAKING，需联调））｜ 语雀-决策记录.md D3 ｜ 完善文档 05-数据落库与掌握度.md
