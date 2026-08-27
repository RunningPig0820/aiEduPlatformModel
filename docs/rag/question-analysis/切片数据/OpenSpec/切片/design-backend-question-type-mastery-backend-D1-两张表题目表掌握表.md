# 两张表——题目表（事实源）+ 掌握表（聚合结果）

> summary: 题目表（事实源）+掌握表（聚合结果）两表分离，改折扣/信号重算聚合即可，题目证据不丢。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-question-type-mastery-backend-D1-两张表题目表掌握表.md
> 类别：数据存储

---

### Decision 1：两张表——题目表（事实源）+ 掌握表（聚合结果）

> 检索摘要：题目表（事实源）+掌握表（聚合结果）两表分离，改折扣/信号重算聚合即可，题目证据不丢。

```
t_student_question_record        t_student_topic_mastery（改造）
  id, student_id                   id, student_id
  content（题目文本）                topic_key（canonical，唯一）
  source（ai/bank）                 topic_label
  topic_label（原始/归一）           mastery（连续 0-100，累计平均）
  score（0.0/0.5/1.0 × 打折）       train_count
  hint_count, answer_request_count  source（ai/bank）
  session_id, created_at            updated_at
```

- **题目表是事实源**：每道题一条记录，含对错信号与引导轮数，可回查。
- **掌握表是聚合结果**：canonical key + 累计平均。两张表隔离「题目证据」与「聚合值」——后续改折扣系数/信号映射，重算聚合即可，题目证据不丢。
- **掌握表改造 vs 新表**：改造现有 `t_student_topic_mastery`（加 `source`/`train_count`，`mastery_level` 语义从「置信度」改「正确率累计」）。历史数据量小：保留旧值作初始正确率、`train_count=1`（平滑过渡）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-question-type-mastery-backend.md`（§Decision 1）｜ 语雀-决策记录.md D18 ｜ 完善文档 05-数据落库与掌握度.md
