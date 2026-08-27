# getMastery 契约 BREAKING

> summary: getMastery 的 masteryLevel 从离散四档（0/25/50/75）改连续百分比 0-100，新增 source/trainCount；后端加新字段不删旧，前端分桶保留四档视觉。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-前端联调问题单-问题15-getMastery契约BREAKING.md
> 类别：开发难点
> 状态：✅ 已修复（方案定稿）

---

### 问题15：getMastery 契约 BREAKING（四档 → 连续百分比）
> 状态：✅ 已修复（方案定稿）`前端需适配`
> 检索摘要：getMastery 的 masteryLevel 从离散四档（0/25/50/75）改连续百分比 0-100，新增 source/trainCount；后端加新字段不删旧，前端分桶保留四档视觉。

| 属性 | 内容 |
|---|---|
| 问题标题 | getMastery 契约 BREAKING（masteryLevel 语义变更） |
| 现象 | 前端按四档消费 masteryLevel，后端改为连续百分比 |
| 触发流程 | GET /students/{id}/mastery 返回 masteryLevel 0-100 + source + trainCount |
| 根因 | 掌握度算法从离散四档改累计平均正确率，语义变连续（D3） |
| 修复方案 | 加新字段不删旧（向后兼容）；前端分桶保留四档视觉（<25 待巩固 / 25-50 练习中 / 50-75 偏稳 / ≥75 已掌握）`前端需适配` |
| 状态 | ✅ 已修复（方案定稿） |
| 证据 | design-backend-question-type-mastery Decision 7；design-frontend-question-type-mastery Decision 8 |

> 证据：详见 `1.语雀/语雀-前端联调问题单.md`（§问题15）｜ 语雀-决策记录.md D3 ｜ 完善文档 05-数据落库与掌握度.md
