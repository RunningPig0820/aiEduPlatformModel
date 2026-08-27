# 知识点匹配与图谱点亮 · 前端

## Why

后端 `kp-matching-lightup` 已把「题型→教材知识点解析 + 掌握度点亮」整条链路做完——`POST /api/kp/resolve`、增强后的 `GET /api/students/{id}/mastery`（已含 `status`/`confidence`）、`GET/POST /api/kg/aliases/pending`、`GET /api/students/{id}/pending-kps`、`POST /api/kp/vote` 均已实现，并本期补齐题型库聚合（`QuestionType`/`QuestionTypeKp`）。但前端只有 admin 图谱页，学生端没有任何掌握度展示。

更关键的是：**当前掌握度的主体搞错了**。整条链路的掌握度信号（Python `decide` 输出 `mastery_signals` → `kp_label` → `kpKey`）都落在**知识点**粒度上——但学生真正掌握的是**题型**（如「鸡兔同笼」），不是知识点（如「二元一次方程」）。学会「鸡兔同笼」不代表掌握了「二元一次方程」；题型是掌握度的直接观测主体，知识点是题型经「题型→知识点映射」**派生**出来的结果。

需要把掌握度模型纠正为「**题型为主体、知识点派生**」，并补上学生端展示，让后端已落的数据被看见、被用完。

## What Changes

- **掌握度子视图**（学习报告下）：改为**题型**四类明细——已掌握/练习中/待巩固/待确认的**题型**（不是知识点），分页；**点某题型展开它派生的知识点**（题型→知识点映射，占比 + 年级分布）——本期主功能「题型分析」合并进本页。
- **知识点总览子视图**（学习报告下）：改为**题型派生的知识点**——全量知识地图（学段→章节→知识点），知识点按「被已掌握题型派生覆盖的程度」着色、未覆盖灰占位，分页 + 可切换知识图谱点亮视图。
- **KnowledgeGraph 组件掌握度叠加模式**：新增可选 `masteryMap` prop，`textbook_kp`/`kp` 节点按派生覆盖度重着色，不影响 admin 图谱页。
- **AI答疑低置信澄清**：`resolve` 低置信时渲染「你想学哪个」非阻塞澄清卡（题型候选 + 跳过），选概念调 `vote` 落 `student_vote`、跳过弃权。
- **API 封装补齐**：`tutoring.js`/`kg.js` 补 `pendingKps`、`resolveKp`、`voteKp`，以及题型掌握度/全量知识点分页接口封装。
- **管理端挂起审核 UI 本期不做**（后端接口已就绪，后续挂现有图谱页）。

## Capabilities

### New Capabilities

- `student-mastery-lightup`: 学生端掌握度展示——学习报告总纲（摘要）+ 掌握度子视图（**题型**四类明细）+ 知识点总览子视图（**题型派生**的全量知识地图）；掌握度主体是题型、知识点派生。
- `kg-mastery-lightup`: 知识图谱组件掌握度叠加模式——按 `masteryMap` 重着色知识点节点（派生覆盖度 + 疑似虚线），admin 图谱页隔离。
- `kp-clarification`: AI答疑低置信澄清卡——「你想学哪个」非阻塞交互（题型候选 + vote 提交）。
- `kp-question-type-analysis`: 题型→知识点派生关系——学生掌握的题型 + 点题型展开派生知识点（占比/年级分布），合并进掌握度页，本期主功能。

### Modified Capabilities

<!-- 无既有 spec 需求变更：均在新增展示层，不改动既有图谱/答疑行为。 -->

### 后续（本期不做）

- `kp-pending-review`（管理端挂起审核队列）：后端 `pending`/`confirm` 接口已就绪，本期前端不做，后续挂现有 `/admin/knowledge-graph` 页。
- 错题本自身的「错题列表」页（错题列表本身仍 pending）。
- 变式题生成等其他消费方。

## Impact

- **前端（主）**：学习报告总纲页 + 掌握度（题型明细 + 点题型展开派生知识点）/知识点总览（题型派生）两个子视图；`KnowledgeGraph` 加 mastery 叠加；`AiQa`/`KpChips` 接澄清卡；`routes.jsx` 学生菜单改造（错题本不再挂题型分析）+ 新路由；`tutoring.js`/`kg.js` 补 API 封装。
- **后端（需配合）**：**掌握度模型纠正**——掌握度信号从「知识点」粒度（`MasterySignal.kpLabel` → `kpKey`）翻转为「题型」粒度（题型为主体），知识点掌握度由「题型→知识点映射」(`QuestionTypeKp`，ratio 占比) **派生**。此外仍需：① 题型掌握度/知识点派生接口；② 按学段列全量知识点 + 分页接口；③ 分页列题型 + 题型→关联知识点接口。其余 resolve / vote / pending / confirm 已实现。
- **数据契约**：消费题型掌握度（`topicKey`＝题型名 + `topicLabel` + `masteryLevel` 离散四档 {0,25,50,75} + `status`/`confidence`）、知识点派生覆盖度（`kpUri` + `coverage` 0-75 + `masteryLevel` 四档 + `status`/`confidence`）、题型→知识点派生关系（`QuestionTypeKp`：kpUri/kpLabel/gradeRange/ratio/hitCount）、`PendingKpAliasDTO`、`KpResolveDTO`（含 `candidates`）、`vote` 请求 `{topicLabel, selectedLabel}`（失败返回 10003）；全量知识点分页 `page`/`size` + `total`。
