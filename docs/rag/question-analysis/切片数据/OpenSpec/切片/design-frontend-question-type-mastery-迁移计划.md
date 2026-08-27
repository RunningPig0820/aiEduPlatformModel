# 迁移计划

> summary: 迁移：后端题目表+向量+聚类+掌握表+契约变更→前端列式化+分桶+跳转→联调；回滚加新字段不删旧。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-question-type-mastery-迁移计划.md
> 类别：架构设计

---

### 迁移计划

> 检索摘要：迁移：后端题目表+向量+聚类+掌握表+契约变更→前端列式化+分桶+跳转→联调；回滚加新字段不删旧。

1. 后端：题目表 + 向量存储 + 定时聚类 + 掌握表聚合 + `getMastery` 契约变更。
2. 前端：掌握度页列式化 + 分桶映射 + 跳转题目；知识点总览去掉覆盖度着色；题型分析页不动。
3. 联调：AI 答疑做题 → 题目落库 → 聚类 → 掌握度百分比更新 → 掌握度页展示 → 跳转题目。
4. 回滚：掌握度页可回退到四档卡片；`getMastery` 契约加新字段而非删旧字段（向后兼容）。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-question-type-mastery.md`（§迁移计划）
