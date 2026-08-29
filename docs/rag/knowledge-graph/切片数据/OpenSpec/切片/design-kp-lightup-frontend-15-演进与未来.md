# 演进与未来

> summary: 演进与未来
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kp-lightup-frontend-15-演进与未来.md
> 类别：未来演进

> 检索摘要：知识点点亮前端迁移计划六步（补 API 封装→KnowledgeGraph 加 masteryMap 灰度验证 admin 不变→学习报告三视图菜单两级化→答疑澄清卡→后端模型纠正到位后联调→回滚关学生新路由不碰后端）；Open Questions 均已关闭（题型分析并入掌握度页、派生覆盖度契约同时返回 coverage 与离散四档）。

**迁移计划**
1. 补 API 封装（题型掌握度 / 知识点派生覆盖度 / `pendingKps` / `resolveKp` / `voteKp` + 全量知识点分页）——纯前端，无迁移。
2. `KnowledgeGraph` 加 `masteryMap` 叠加模式（admin 不传，零影响）→ 灰度验证 admin 图谱页不变。
3. 学习报告总纲 + 掌握度（题型）/知识点总览（题型派生）/题型分析，菜单两级化。
4. 答疑澄清卡（resolve + vote）——依赖后端 vote 接口。
5. 后端模型纠正（掌握度主键 → 题型）+ 派生接口到位后联调。
6. 回滚：关掉学生新路由即回退，不碰后端。

**Open Questions（均已关闭）**
- 题型分析导航归属：掌握度（题型）与题型分析（题型→知识点）合并为一页——掌握度页点题型展开派生知识点，不再设独立「题型分析」子菜单，也不挂错题本下。
- 知识点派生覆盖度契约：后端同时返回覆盖度 coverage（0-75）与离散四档（masteryLevel 0/25/50/75）及 status/confidence，前端把参数都拿到，按场景选用（列表/图谱着色用离散档，详情用连续覆盖度）。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-matching-lightup-frontend.md`（§Migration Plan/§Open Questions）
