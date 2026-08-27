# 迁移计划

> summary: 前端补 API 封装与 KnowledgeGraph masteryMap 叠加、学习报告三视图、答疑澄清卡，联调后端模型纠正，可关路由回滚不碰后端。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-frontend-kp-matching-lightup-frontend-迁移计划.md
> 类别：架构设计

---

### Migration Plan

> 检索摘要：前端补 API 封装与 KnowledgeGraph masteryMap 叠加、学习报告三视图、答疑澄清卡，联调后端模型纠正，可关路由回滚不碰后端。

1. 补 API 封装（题型掌握度 / 知识点派生覆盖度 / `pendingKps` / `resolveKp` / `voteKp` + 全量知识点分页）——纯前端，无迁移。
2. `KnowledgeGraph` 加 `masteryMap` 叠加模式（admin 不传，零影响）→ 灰度验证 admin 图谱页不变。
3. 学习报告总纲 + 掌握度（题型）/知识点总览（题型派生）/题型分析，菜单两级化。
4. 答疑澄清卡（resolve + vote）——依赖后端 vote 接口。
5. 后端模型纠正（掌握度主键 → 题型）+ 派生接口到位后联调。
6. 回滚：关掉学生新路由即回退，不碰后端。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-matching-lightup-frontend.md`（§Migration Plan）
