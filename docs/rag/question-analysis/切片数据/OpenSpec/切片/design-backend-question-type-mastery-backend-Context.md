# 背景：掌握度数据底盘零散

> summary: 掌握度数据底盘零散：无题目记录、题型名自由文本裂行、无题库零锚点、向量无 Java SDK，需建可追溯正确率底盘。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-question-type-mastery-backend-Context.md
> 类别：项目介绍

---

### 背景：掌握度数据底盘零散

> 检索摘要：掌握度数据底盘零散：无题目记录、题型名自由文本裂行、无题库零锚点、向量无 Java SDK，需建可追溯正确率底盘。

- **信号形态**：`decide` 逐轮输出三档信号（mastered/practicing/struggling），`applyMasteryAndErrors` 取 **max 单调不减**（答错不降分，置信度视角）。算不出「练了几道、答对几道」的正确率。
- **题型名是 LLM 自由文本**：`t_student_topic_mastery` 的 key 是 `TopicKeyNormalizer.normalize(label)`（字符串级）。「一元二次方程」和「解一元二次方程」裂成两行。聚合 merge（kp_uri 重叠 ≥0.7）只影响题型库，**不回流掌握表**。
- **零题目状态**：后端明确不记录题目内容（`DecideContext` 注释），题目文本只存在于会话 history 里。
- **掌握信号唯一来源 = AI 答疑**（题型分析只记题目不产生对错）。
- **无题库、零锚点**：没有预置的题型分类表，canonical 由学生题目动态涌现。
- **COS 向量检索无 Java SDK**：只有 Python/Go SDK（`CosVectorsClient`/`VectorService`），向量操作走 Python 桥。

> 证据：详见 `2.OpenSpec design 决策/design-backend-question-type-mastery-backend.md`（§背景：掌握度数据底盘零散）｜ 语雀-决策记录.md D2/D3/D18/D19
