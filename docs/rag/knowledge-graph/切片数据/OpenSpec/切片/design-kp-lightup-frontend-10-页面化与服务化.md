# 页面化与服务化：背景与关键数据契约

> summary: 页面化与服务化（背景与关键数据契约）
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kp-lightup-frontend-10-页面化与服务化.md
> 类别：操作流程

> 检索摘要：知识点点亮前端：后端 kp-matching-lightup 解析管线、掌握度增强、挂起审核、题型库聚合均已实现，前端只缺展示层；关键契约 mastery_level 仅 0/25/50/75，图谱节点与掌握度 kp 同源，知识点派生覆盖度同时返回 coverage 0-75 与离散四档；核心模型纠正为掌握度主体=题型、知识点由 QuestionTypeKp ratio 派生。

**文档定位**：本文为原始 spec 文档的 RAG 结构化重构版本，属设计阶段素材，同时包含已落地、构想未实现、待决策内容；业务真实实现以权威度 0.8 的 canonical 真相源文档为准。本文件独立完整，内容不拆分到外部 canonical 文档。

**背景：后端已完成，前端缺展示层**
- `kp-matching-lightup`（后端仓库）的解析管线、掌握度增强、挂起审核、题型库聚合均已实现，前端只缺展示层。
- 现状：`tutoring.js` 已有 `getMastery(studentId)`（返回 `items[]`，后端已含 `status`/`confidence`），但无人调用；admin 图谱页 `/admin/knowledge-graph` 已存在（`KnowledgeGraphPage.jsx`），组件 `KnowledgeGraph.jsx`（ReactFlow + dagre，按类型配色）；学生菜单已有「学习报告」占位、「错题本」占位，未接页面；答疑页 `AiQa` 已有 `KpChips`（渲染 `meta.eval.masterySignals` 绿/黄/红 badge）。

**关键数据契约（后端已确认）**
- 图谱节点 `textbook_kp` 的 `id` 与 `data.uri` 均为 TextbookKP URI，与掌握度 item 的 kp 标识同源，可直接匹配。
- `mastery_level` 取值仅 `{0, 25, 50, 75}` 四档离散值。
- 题型库：`QuestionType`（topicLabel、status CANDIDATE/STABLE、hitCount）+ `QuestionTypeKp`（kpUri、kpLabel、gradeRange、ratio 占比、hitCount），由聚合任务 `KpQuestionTypeAggregationService` 沉淀。
- 知识点派生覆盖度契约：后端同时返回「覆盖度 coverage（0-75，等于 Σ 题型掌握度×ratio，与题型掌握度同量纲）」与「离散四档（masteryLevel 0/25/50/75）」及 `status`/`confidence`，前端全部消费（着色用离散档，详情进度条用 coverage，百分比展示 coverage/75*100）。

**核心模型纠正：掌握度主体 = 题型，知识点派生**
- 当前（错）：整条掌握度链路以知识点为主键——Python `decide` 输出 `mastery_signals[].kp_label` → `TutoringKpResolver` 解析成 TextbookKP URI → `StudentKpMastery`（`student_id + kp_key` 唯一）→ `MasteryItemDTO`（`kpKey` 主键）。把「会做某类题」直接当成「掌握某个知识点」。
- 纠正（对）：学生掌握的是题型，不是知识点。学会「鸡兔同笼」不等于掌握「二元一次方程」。掌握度主体应是题型；知识点是题型经「题型→知识点映射」派生的结果。
- 数据流：学生做题（decide 输出 mastery_signals）→ 题型掌握度（主体：题型 topicLabel，mastered/practicing/struggling → 75/50/25）→ 题型→知识点映射（QuestionTypeKp：kpUri + ratio 占比）→ 知识点派生覆盖（某知识点 = Σ 覆盖它的题型的掌握度 × ratio）→ 知识点总览（全量知识点，按派生覆盖度着色）。
- 后端依赖（需配合）：掌握度信号从「知识点」粒度翻转为「题型」粒度（`MasterySignal`/`StudentKpMastery` 主键由 `kpKey` 改为题型标识 `topicKey`＝题型名），知识点掌握度由 `QuestionTypeKp`（ratio）派生。前端依赖「题型掌握度」与「知识点派生覆盖度」两个新契约。
- 旁证：`pending-kps` 返回的 `PendingKpAliasDTO` 本就是「题型（topicLabel）+ 疑似知识点（kpLabel）」结构——「待确认」天然是「某个题型的知识点归属不确定」，与题型为主体的模型一致，比知识点为主键更自洽。

**Goals / Non-Goals**
- Goals：学生端学习报告总纲（摘要卡）+ 三个子视图——掌握度（题型四类明细）、知识点总览（题型派生的全量知识地图）、题型分析（题型→知识点派生关系，本期主功能）；`KnowledgeGraph` 组件可复用叠加掌握度，admin 图谱页零影响；答疑低置信澄清卡（resolve + vote 两步）落地。
- Non-Goals：管理端挂起审核 UI 本期不做；教师端本期不做；错题本自身的「错题列表」页本期不做；不改权威图谱、不做同步/统计功能。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-matching-lightup-frontend.md`（§文档说明/§Context/§核心模型纠正/§Goals-Non-Goals）
