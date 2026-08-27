# 目标与非目标

> summary: 目标=analyze-question 端点+题型库别名合并+题目理解端口抽象；非目标=管理端审核/题库种子/批量扫题/Python 端点/掌握度变体合并。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-Goals-Non-Goals.md
> 类别：项目介绍

---

### 目标与非目标

> 检索摘要：目标=analyze-question 端点+题型库别名合并+题目理解端口抽象；非目标=管理端审核/题库种子/批量扫题/Python 端点/掌握度变体合并。

**Goals:**
- `POST /api/kp/analyze-question { text }`：题目文本 → 识别题型名 → 返回关联知识点清单；**纯分析不写 obs**；PENDING 不报错、携带澄清候选。
- 题型库别名合并：相似题型名收敛到 canonical 题型 + 同一 kp 分布；`resolve`②/`vote`/聚合均按别名命中，聚合阈值不再被变体稀释。
- 题目理解端口抽象（domain），Java LLM 为默认实现，Python 独立端点可替换。

**Non-Goals:**
- 管理端/老师端全局审核（`kp-pending-review`）——本期学生确认只走个人观测。
- 题库域已有题型标签当种子观测（Q3 跨来源）——后续阶段，本期不为题库域类型建模。
- proactive 批量扫题库自动补题型（Q4）——后续阶段。
- Python 独立题目理解端点——本期只留端口，不跨仓库。
- 掌握度层变体合并（`t_student_topic_mastery` 的 topic_key 分裂）——kp-matching-lightup Decision 17 归一化已折叠硬变体（全角/空白/末尾标点），语义级同义词聚类留大数据阶段。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§目标与非目标）｜ 完善文档 08-演进路线.md
