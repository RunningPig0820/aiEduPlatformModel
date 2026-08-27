# 目标与非目标

> summary: 目标=建题目→题型掌握数据底盘（采集→归一→累计平均聚合），非目标=题型知识点关联/相似题/题库/定时任务。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-question-type-mastery-backend-Goals-Non-Goals.md
> 类别：项目介绍

---

### 目标与非目标

> 检索摘要：目标=建题目→题型掌握数据底盘（采集→归一→累计平均聚合），非目标=题型知识点关联/相似题/题库/定时任务。

**Goals:**
- 建立「题目 → 题型掌握」完整数据底盘：采集 → 题型名归一 → 累计平均聚合。
- 掌握度可追溯：每道题有记录，掌握度 = 累计平均正确率（可解释）。
- 掌握表 key 从源头归一（canonical），「一元二次方程/解一元二次方程」不裂行。
- 掌握度页列式化数据支撑：题型 / 来源 / 掌握% / 训练数 / 跳转题目。

**Non-Goals（本期明确不做）：**
- 题型↔知识点关联、知识点总览覆盖度着色（前端断联，`kp-coverage` 接口保留但不消费）。
- **相似题存储/检索**：题目向量本期不落库；本期向量库只存「canonical 题型名 → 向量」，用于题型名归一。
- 题库建设（`t_question` 题库域已有，与「学生作答记录」是两回事）。
- 全局题型库（跨学生沉淀 canonical）——本期归一是 per 全局的题型名，掌握度仍 per 学生。
- **只记录「题目→题型」**：本期不新增「题型→知识点」数据写入；`t_kp_derived_obs`/`t_kp_question_type`/`t_kp_question_type_alias` 保留不动、独立演进。
- **题型↔知识点自动关联不做**：入口不自动关联知识点——查表只读 + 独立维护；obs 共现自动聚合/挂起/澄清批处理本期停用。
- **不做定时任务**：聚合/维护/批量聚集全部按钮手动触发，不新增 `@Scheduled`。

> 证据：详见 `2.OpenSpec design 决策/design-backend-question-type-mastery-backend.md`（§目标与非目标）｜ 语雀-决策记录.md D3/D8/D18
