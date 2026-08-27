# analyze-question接口契约

> summary: analyze-question 契约：编排=理解→全候选遍历→前2候选消歧（LLM 预算收敛）→PENDING+candidates 镜像校验；WEAK 降级不冒充 RESOLVED。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D5-analyze-question接口契约.md
> 类别：开发难点

---

### D5：analyze-question 接口契约

> 检索摘要：analyze-question 契约：编排=理解→全候选遍历→前2候选消歧（LLM 预算收敛）→PENDING+candidates 镜像校验；WEAK 降级不冒充 RESOLVED。

#### 端点与响应结构

`POST /api/kp/analyze-question { text }` → `ApiResponse<QuestionAnalysisDTO>`：

```json
{
  "topicLabel": "鸡兔同笼问题",
  "status": "RESOLVED",          // RESOLVED / PENDING
  "confidence": 85,               // 0-100，PENDING 为 0
  "knowledgePoints": [
    { "kpUri": "…textbook…", "kpLabel": "鸡兔同笼", "gradeRange": "4-6", "ratio": 0.8 }
  ],
  "candidates": []                // PENDING 时填充，RESOLVED 为空
}
```

#### 编排流程

编排（`KpQuestionAnalysisAppService.analyze(text, studentId)`，确定性靠功能 + 提示词，**不依赖缓存**）：

```
① understand(text, grade) → 候选题型名 [t1, t2, …]（空 → PENDING 无候选）
② 遍历全部候选：任一 findByTopicLabelOrAlias(ti) 命中 → status=RESOLVED，
     knowledgePoints=该题型全部关联分布（数据驱动权威，结果与候选顺序无关）
③ 前 LLM_RESOLVE_BUDGET=2 个候选走 resolveReadOnly（镜像权威）：
     首个 RESOLVED 且非 WEAK → 单点 RESOLVED（短路）
     WEAK/PENDING → 收集候选（WEAK 的 kpLabel + PENDING candidates，镜像校验后）
④ 全无权威命中 → PENDING + candidates（candidates 已镜像校验，保证 vote 不 10003）
     + 落 PENDING obs「挂起来」（upsertPendingIfAbsent）
```

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D5）｜ 完善文档 02-题型分析主流程怎么走.md ｜ 坑档案 J-QT5
