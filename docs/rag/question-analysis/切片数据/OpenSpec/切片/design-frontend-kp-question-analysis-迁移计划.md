# 迁移计划

> summary: 迁移：analyze 端点→前端 API 封装→菜单路由→分析页→联调；回滚关路由即可不碰后端。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-kp-question-analysis-迁移计划.md
> 类别：架构设计

---

### 迁移计划

> 检索摘要：迁移：analyze 端点→前端 API 封装→菜单路由→分析页→联调；回滚关路由即可不碰后端。

1. 后端 `analyze-question` 端点（从 resolve 管线加「题目理解」前置，或独立复用识别能力）。
2. 前端 API 封装：`analyzeQuestion(text)`。
3. 智能练习菜单翻 active + 挂「题型分析」子菜单 + 路由。
4. 题型分析页：贴题输入 + 结果清单 + 确认交互（复用 vote）。
5. 联调：贴题 → 分析 → 展示 → 确认 → 查 obs 落库 → 聚合（手动/次日）。
6. 回滚：关掉「智能练习」路由即回退，不碰后端。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-question-analysis.md`（§迁移计划）
