# 迁移计划

> summary: 迁移：V16 别名表→domain 端口→infra 实现→application 编排→analyze 端点；回滚关端点删别名表即可，无破坏性变更。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-迁移计划.md
> 类别：架构设计

---

### 迁移计划

> 检索摘要：迁移：V16 别名表→domain 端口→infra 实现→application 编排→analyze 端点；回滚关端点删别名表即可，无破坏性变更。

1. V16 迁移：`t_kp_question_type_alias`（learning 库，含 UNIQUE(alias_label) + FK(question_type_id) + 索引）。**Flyway 关闭，需手动执行**（同 kp-matching-lightup 教训）。
2. domain：`QuestionUnderstandingPort`、`QuestionTypeAlias` 实体、仓储接口 `findByTopicLabelOrAlias`/`findTopTopicLabels`/别名 upsert。
3. infra：`KpQuestionAnalyzer`（LLM 实现）、别名 PO/Mapper/仓储实现（`@DS("learning")`）。
4. application：`KpQuestionAnalysisAppService`；`TutoringKpResolverImpl` 抽 `persistObs`；聚合 `aggregateTopic` 加别名合并。
5. interface：`KpResolutionController` 加 `POST /api/kp/analyze-question`。
6. 回滚：新增端点/表，无破坏性变更；回退关端点 + 删别名表即可，`resolve`/`vote`/题型库接口契约不变。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§迁移计划）
