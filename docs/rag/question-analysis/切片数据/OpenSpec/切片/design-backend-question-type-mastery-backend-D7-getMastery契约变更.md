# getMastery 契约变更

> summary: getMastery 契约 BREAKING：masteryLevel 四档改 0-100 连续百分比，新增 source/trainCount，前端分桶保留四档视觉。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-question-type-mastery-backend-D7-getMastery契约变更.md
> 类别：开发难点

---

### Decision 7：`getMastery` 契约变更（BREAKING，前端联调）

> 检索摘要：getMastery 契约 BREAKING：masteryLevel 四档改 0-100 连续百分比，新增 source/trainCount，前端分桶保留四档视觉。

```
GET /students/{id}/mastery
响应 items[]:
  topicKey / topicLabel
  masteryLevel：0-100 连续百分比（原 0/25/50/75 离散四档）  ← BREAKING
  source：'ai' | 'bank'
  trainCount
  status：RESOLVED / PENDING（保留 PENDING=obs 有但未确认）
```

- **前端分桶保留四档视觉**（<25 待巩固 / 25-50 练习中 / 50-75 偏稳 / ≥75 已掌握）。
- **向后兼容**：加新字段而非删旧字段；`masteryLevel` 语义变更用版本或文档标 BREAKING。
- **`kp-coverage` 派生仍可工作**：知识点覆盖度 = clamp(Σ(题型掌握度×ratio), 0, 75)——连续正确率输入，派生逻辑不变（仅前端不再消费）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-question-type-mastery-backend.md`（§Decision 7）｜ 语雀-决策记录.md D3/D14 ｜ 完善文档 05-数据落库与掌握度.md
