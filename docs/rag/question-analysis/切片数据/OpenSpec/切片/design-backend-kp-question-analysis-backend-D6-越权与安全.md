# 越权与安全

> summary: analyze-question 需 STUDENT 登录（未登录 10004/非学生 20004），无管理功能暴露，findTopTopicLabels 只读。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D6-越权与安全.md
> 类别：开发难点

---

### D6：越权与安全

> 检索摘要：analyze-question 需 STUDENT 登录（未登录 10004/非学生 20004），无管理功能暴露，findTopTopicLabels 只读。

`analyze-question` 用 `TutoringAuth.requireStudent(session)`（未登录 → 10004，非 STUDENT → 20004），与 api.md「需要登录（STUDENT）」契约一致。取不到年级时降级纯 LLM 题目理解（无年级锚，resolve 已有降级）。无管理功能暴露。`findTopTopicLabels` 只读不越权。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D6）｜ 完善文档 04-防作弊与异常防护.md
