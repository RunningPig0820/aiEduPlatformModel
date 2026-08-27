# 开放问题

> summary: 开放项已全部决：提示后答对信号用 allowedType/answerRequestCount 推断、打折 per 题型配置化、embedding text-embedding-v3、per 学生聚类。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-question-type-mastery-开放问题.md
> 类别：未来演进

---

### 开放问题（全部已决，后端已实现）

> 检索摘要：开放项已全部决：提示后答对信号用 allowedType/answerRequestCount 推断、打折 per 题型配置化、embedding text-embedding-v3、per 学生聚类。

- **~~decide 是否输出「提示后答对」信号（`hinted`）？~~ 已决**：后端**不加字段**，用 `allowedType==HINT/APPROACH || answerRequestCount>0` 推断（`TutoringAppService.applyMasteryAndErrors`），`ScoreMapper.baseScore` 映射：直接答对 1.0 / 引导后答对 0.5 / 答错 0.0。前端无需改——题目列表 `score` 已是 0.5，徽标直接消费。
- **~~打折系数的作用域~~ 已决**：**per 题型**（`trainCount` = 该题型已训练数，本次为第 `trainCount+1` 题），第1题 0.7 / 第2题 0.8 / 第3题起 1.0，入 `application.yml`（`ai-edu.tutoring.signal.discount-*`）配置化，作用于 score 不作用于结果。
- **~~题目向量化的 embedding 模型~~ 已决**：dashscope `text-embedding-v3`（后端 Python 向量桥复用）。
- **~~per 学生聚类 vs 全局题型库~~ 已决**：本期 **per 学生**（canonical 由 `TopicLabelAggregationService.aggregate` per student 动态锚定）；全局题库（跨学生沉淀）后续独立。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-question-type-mastery.md`（§开放问题（全部已决，后端已实现））｜ 完善文档 05-数据落库与掌握度.md ｜ 完善文档 06-题型动态聚集与向量.md
