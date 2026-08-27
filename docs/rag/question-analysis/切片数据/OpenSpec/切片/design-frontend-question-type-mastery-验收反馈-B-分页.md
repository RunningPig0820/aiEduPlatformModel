# 验收反馈 B：分页

> summary: 掌握度列表锁定后端分页：?page=&size= 请求式翻页，total 完整计数，移除本地全量切页。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-question-type-mastery-验收反馈-B-分页.md
> 类别：操作流程

---

### 验收反馈 B：掌握度列表加分页（后端分页）

> 检索摘要：掌握度列表锁定后端分页：?page=&size= 请求式翻页，total 完整计数，移除本地全量切页。

- **反馈**：掌握度列表需要分页。
- **决策**：**后端分页**——题型会越来越多（聚类后的 canonical 题型持续增长），前端全量拿到后渲染/切页会撑不住，锁定后端分页。
- **契约**：`GET /students/{id}/mastery?page=&size=` → `{ studentId, page, size, total, items }`；`total` 完整计数（RESOLVED + PENDING 拼接后分页）。**转后端**（tasks 4.5）。
- **前端**：请求式分页（翻页带参调后端），移除本地 `slice` 全量切页（tasks 12.2）。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-question-type-mastery.md`（§验收反馈 B：掌握度列表加分页（后端分页））
