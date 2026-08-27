# mastery_snapshot脱钩
> summary: mastery_signals 不再优先复用掌握度快照候选，题型与知识点快照不同源；mastery_snapshot 保留在契约里降级为背景参考或不提。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-决策记录-D25-mastery_snapshot脱钩.md
> 类别：数据关联

---

### D25 mastery_snapshot 脱钩（题型与知识点快照不同源）
> 检索摘要：mastery_signals 不再优先复用掌握度快照候选，题型与知识点快照不同源；mastery_snapshot 保留在契约里降级为背景参考或不提。

| 属性 | 内容 |
|---|---|
| 背景 | 旧 mastery_snapshot 是知识点 label 快照，无法为题型提供候选 |
| 演进 | 快照优先复用 → 脱钩（保留字段、降级为背景参考） |
| 拍板理由 | 题型与知识点快照不同源，知识点快照不能给题型候选；question_kps 仍可参考快照（继续知识点） |
| 系统影响 | Java 契约不动、字段默认空；prompt 中降级为背景参考或不提 |
| 证据 | design-python-ai-tutoring-topic-mastery-signal Decision 3 |

> 证据：详见 `1.语雀/语雀-决策记录.md`（§D25）｜ 完善文档 05-数据落库与掌握度.md
