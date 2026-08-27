# 前端范围降级

> summary: 前端本期降级：贴题→识别题型核心，知识点顺带展示不强求，确认/搜索/待确认闭环转后续独立功能。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D12-前端范围降级.md
> 类别：业务视角

---

### D12：前端范围降级

> 检索摘要：前端本期降级：贴题→识别题型核心，知识点顺带展示不强求，确认/搜索/待确认闭环转后续独立功能。

前端本期降级为「**贴题 → 识别题型（核心）+ 知识点顺带参考（有则展示，无则不强求）**」，知识点关联的确认/搜索/待确认闭环转后续独立功能「题型↔知识点关联完善」。

**后端零改动**：现有 analyze-question（含 D8 池约束恒非空）是严格超集，满足降级后范围；D8 池约束选择 / D9 keyword 搜索 / 聚合手动触发已实现，供后续独立功能直接复用，非本期待办。掌握度主体=题型、知识点覆盖度派生（不与本题型知识点直接耦合）与前端「掌握度=掌握的题型」定位一致。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D12）｜ 完善文档 08-演进路线.md
