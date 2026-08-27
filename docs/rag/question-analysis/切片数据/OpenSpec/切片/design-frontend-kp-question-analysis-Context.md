# 背景

> summary: 题型分析页前端：现有聚合/vote/接口可复用，缺口=题目→题型→知识点无独立 REST，需建单题分析页。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-kp-question-analysis-Context.md
> 类别：项目介绍

---

### 背景：老方案已就绪，缺口是"题目文本→识别题型→关联知识点"

> 检索摘要：题型分析页前端：现有聚合/vote/接口可复用，缺口=题目→题型→知识点无独立 REST，需建单题分析页。

- **老方案已就绪**（`kp-matching-lightup-frontend`）：题型库聚合任务（`KpQuestionTypeAggregationService`，凌晨 3:17 扫 obs → 沉淀 `QuestionType`/`QuestionTypeKp`）、题型库分页 + 关联知识点接口、`vote` 接口（落 `STUDENT_VOTE` 观测）、`resolve` 接口（label → 知识点解析，PENDING 返回 candidates）。
- **聚合任务已消费学生确认**：`selectResolved()` = `WHERE kp_uri IS NOT NULL`（不看 source），学生 `vote` 落 `RESOLVED + STUDENT_VOTE` 观测（kp_uri 非空），天然进聚合 → 跨学生达阈值（≥3 学生 / ≥5 命中）沉淀题型库。
- **现有接口**（复用）：`POST /api/tutoring/ocr`（拍题识别文本）、`GET /api/kp/question-types`（题型库分页）、`GET /api/kp/question-types/{id}/knowledge-points`（题型→知识点）、`POST /api/kp/vote`。
- **缺口**：`resolve` 是 **label 级**（需先知道题型名）；题目理解只在答疑 Python `decide` 内（SSE 会话绑定）。无「题目文本 → 识别题型 → 关联知识点」的独立 REST 接口。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-question-analysis.md`（§背景）｜ 语雀-决策记录.md D20 ｜ 完善文档 02-题型分析主流程怎么走.md
