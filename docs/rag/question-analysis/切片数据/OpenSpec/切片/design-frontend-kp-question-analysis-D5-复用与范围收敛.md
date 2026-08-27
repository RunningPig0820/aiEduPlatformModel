# 复用与范围收敛

> summary: 复用 OCR/题型库/vote，不新增关联表/任务，唯一后端新增 analyze-question。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-kp-question-analysis-D5-复用与范围收敛.md
> 类别：业务视角

---

### 决策 5：复用与范围收敛

> 检索摘要：复用 OCR/题型库/vote，不新增关联表/任务，唯一后端新增 analyze-question。

- OCR（图片题）→ 复用 `POST /api/tutoring/ocr`。
- 题型库浏览（聚合结果展示）→ 复用 `GET /api/kp/question-types` + `/{id}/knowledge-points`。
- 本方案**不新增**题型→知识点关联表/任务，全部消费既有；唯一后端新增是 `analyze-question`。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-question-analysis.md`（§决策 5）｜ 完善文档 02-题型分析主流程怎么走.md ｜ 完善文档 09-业务闭环与两域解耦.md
