# 背景

> summary: 后端 kp-matching-lightup 解析管线与掌握度增强已实现，前端仅缺展示层；关键契约 mastery_level 仅 0/25/50/75，图谱节点与掌握度 kp 同源。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-frontend-kp-matching-lightup-frontend-Context.md
> 类别：项目介绍

---

### Context：后端已完成、前端缺展示层与关键数据契约

> 检索摘要：后端 kp-matching-lightup 解析管线与掌握度增强已实现，前端仅缺展示层；关键契约 mastery_level 仅 0/25/50/75，图谱节点与掌握度 kp 同源。

- **后端已完成**：`kp-matching-lightup`（后端仓库）的解析管线、掌握度增强、挂起审核、题型库聚合均已实现。前端只缺展示层。
- **现状**：
  - `tutoring.js` 已有 `getMastery(studentId)`（返回 `items[]`，后端已含 `status`/`confidence`），但**无人调用**。
  - admin 图谱页 `/admin/knowledge-graph` 已存在（`KnowledgeGraphPage.jsx`），组件 `KnowledgeGraph.jsx`（ReactFlow + dagre，按类型配色）。
  - 学生菜单已有「学习报告」占位、「错题本」占位，未接页面。
  - 答疑页 `AiQa` 已有 `KpChips`（渲染 `meta.eval.masterySignals` 绿/黄/红 badge）。
- **关键数据契约**（后端已确认）：
  - 图谱节点 `textbook_kp` 的 `id` 与 `data.uri` 均为 TextbookKP URI，与掌握度 item 的 kp 标识同源，可直接匹配。
  - `mastery_level` 取值仅 `{0, 25, 50, 75}` 四档离散值。
  - 题型库：`QuestionType`（topicLabel、status CANDIDATE/STABLE、hitCount）+ `QuestionTypeKp`（kpUri、kpLabel、gradeRange、ratio 占比、hitCount）——由聚合任务 `KpQuestionTypeAggregationService` 沉淀。
  - 知识点派生覆盖度契约：后端**同时返回**「覆盖度 coverage（0-75，＝Σ 题型掌握度×ratio，与题型掌握度同量纲）」与「离散四档（masteryLevel 0/25/50/75）」及 `status`/`confidence`，前端全部消费（着色用离散档，详情进度条用 coverage，百分比展示 coverage/75*100）。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-matching-lightup-frontend.md`（§Context：后端已完成、前端缺展示层与关键数据契约）
