# 掌握度信号语义翻转

> summary: mastery_signals 输出题型 label 不输出知识点（学生掌握的是题型），否则污染后端题型库致掌握度/覆盖度/图谱点亮全脏。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-ai-tutoring-topic-mastery-signal-D1-掌握度信号语义翻转.md
> 类别：数据关联

---

### 决策 1：掌握度信号语义翻转（题型为主体，必改）

> 检索摘要：mastery_signals 输出题型 label 不输出知识点（学生掌握的是题型），否则污染后端题型库致掌握度/覆盖度/图谱点亮全脏。

`mastery_signals[].topic_label` 输出**题型**（「鸡兔同笼」「相遇问题」「牛吃草」），**不输出**知识点（「二元一次方程组」「假设法」）。

理由：学生掌握的是题型，不是知识点。知识点掌握度由后端「题型掌握度 × 题型→知识点映射」派生。若 Python 仍输出知识点名，会污染后端题型库 → 掌握度/派生覆盖度/图谱点亮全脏。

> 证据：详见 `2.OpenSpec design 决策/design-python-ai-tutoring-topic-mastery-signal.md`（§决策 1）｜ 语雀-决策记录.md D2/D12
