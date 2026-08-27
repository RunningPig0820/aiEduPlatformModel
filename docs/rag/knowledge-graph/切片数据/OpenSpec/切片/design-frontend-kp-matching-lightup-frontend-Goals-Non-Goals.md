# 目标与非目标

> summary: 目标：学习报告总纲+掌握度（题型）/知识点总览（题型派生）/题型分析三视图，KnowledgeGraph 可叠加掌握度，答疑澄清卡落地；本期不做管理端审核与错题本列表。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-frontend-kp-matching-lightup-frontend-Goals-Non-Goals.md
> 类别：项目介绍

---

### Goals / Non-Goals

> 检索摘要：目标：学习报告总纲+掌握度（题型）/知识点总览（题型派生）/题型分析三视图，KnowledgeGraph 可叠加掌握度，答疑澄清卡落地；本期不做管理端审核与错题本列表。

**Goals:**
- 学生端学习报告总纲（摘要卡）+ 三个子视图：掌握度（**题型**四类明细）、知识点总览（**题型派生**的全量知识地图）、题型分析（题型→知识点派生关系，本期主功能）。
- `KnowledgeGraph` 组件可复用叠加掌握度，admin 图谱页零影响。
- 答疑低置信澄清卡（resolve + vote 两步）落地。

**Non-Goals:**
- 管理端挂起审核 UI 本期不做；教师端本期不做。
- 错题本自身的「错题列表」页本期不做。
- 不改权威图谱、不做同步/统计功能。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-matching-lightup-frontend.md`（§Goals / Non-Goals）
