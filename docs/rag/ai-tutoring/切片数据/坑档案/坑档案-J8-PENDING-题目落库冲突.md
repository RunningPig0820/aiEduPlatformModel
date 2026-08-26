# 坑档案

> summary: 解决PENDING题目落库冲突，修改topic_label可空
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J8. PENDING 题目落库冲突
> 模块: ai-tutoring ｜ 节: 坑档案
> 类别：开发难点

---

### J8. PENDING 题目落库冲突
**1. 问题现象**：答疑 PENDING（题型未识别）题目落库报错——canonical 为 null 无法落库。

**2. 触发流程**：`applyMasteryAndErrors` → 结算分支（SWITCH/isNewQuestion/END/REVEAL，`TutoringAppService.java:771-775`）→ `persistQuestionAttempt`（`:784`）→ `canonical` 计算（`:789-792`）→ `questionRecordRepository.save(...)`（`:805-807`）。

**3. 根因分析**：V17 建表 `topic_label VARCHAR(255) NOT NULL`（`V17__create_t_student_question_record.sql:14`）。PENDING（题型未识别，`masterySignals` 空 → topicLabel null → canonical null）时 INSERT `topic_label=null` → 真实 DB 插入报错。

**4. 排查过程**：从"PENDING 落库报错"反推 → 看 questionRecord save 的 topic_label 来源（canonical 依赖题型识别）→ 确认 PENDING 时 canonical=null 撞上 NOT NULL 约束。

**5. 解决方案 & 改动点**：
- V20 迁移 `topic_label` 改 NULL（canonical=null 照常落库，**信号不丢**；归属后 2.6 批量聚集补）
- `persistQuestionAttempt` 明确 canonical=null 路径：跳过掌握表聚（`:809`），题目表照常 save（`:805-807`）

**6. 面试口述要点**：讲"**未识别数据也要落库**"——PENDING 题型没识别出来不代表这轮作答没价值。技术权衡：topic_label 改可空，先落库保信号，归属后再补聚；宁可存 null 不丢数据。踩坑收获：**业务上"可识别"与"不可识别"的边界要先想清楚，DB 约束别卡住正常流程**。

---
