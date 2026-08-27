# 迁移计划

> summary: 掌握度底盘迁移：spike 标定→表结构→向量初始化→落库链路→聚合改写，回滚无损（加列非删列、向量不接主链路）。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-question-type-mastery-backend-迁移计划.md
> 类别：架构设计

---

### 迁移计划

> 检索摘要：掌握度底盘迁移：spike 标定→表结构→向量初始化→落库链路→聚合改写，回滚无损（加列非删列、向量不接主链路）。

1. **spike**（前置）：embedding 模型选型 + 阈值标定（50~100 真实题型名）。
2. **表结构**：新建 `t_student_question_record`；`t_student_topic_mastery` 加 `source`/`train_count`（`mastery_level` 语义改累计平均）。
3. **向量初始化（Python 侧）**：CosVectorsClient 建索引（768 维 cosine）+ **可选**种子（有知识点池/题型库时预置 embedding 加速收敛）；无则**从零动态积累**（首题建锚，不阻塞）。
4. **落库链路**：AI 答疑/题型分析入口接题目落库 + 聚集 post-process（动态锚定 canonical）。
5. **聚合改写**：`applyMasteryAndErrors` → 题目落库 + 累计平均；`getStudentMastery` → 连续百分比。
6. **接口**：按题型查题目列表；`getMastery` 契约变更（前端联调）。
7. **回滚**：掌握表加列非删列；`getMastery` 旧字段保留；向量库不接主链路（聚集失败回退字符规则 + 原样落库，不阻塞）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-question-type-mastery-backend.md`（§迁移计划）｜ 语雀-决策记录.md D3/D7/D13/D18
