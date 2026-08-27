# mastery_snapshot 脱钩

> summary: mastery_snapshot 脱钩：题型与知识点快照不同源，保留字段降级背景参考，question_kps 仍参考快照。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-ai-tutoring-topic-mastery-signal-D3-mastery-snapshot脱钩.md
> 类别：数据存储

---

### 决策 3：mastery_snapshot 脱钩

> 检索摘要：mastery_snapshot 脱钩：题型与知识点快照不同源，保留字段降级背景参考，question_kps 仍参考快照。

`mastery_signals` 不再「优先复用快照候选」。理由：题型与知识点快照不同源，快照（旧 `t_student_kp_mastery` 知识点 label）无法为题型提供候选。`mastery_snapshot` 保留在 `DecideRequest` 里（Java 契约不动、字段默认空），prompt 中降级为背景参考或不提；`question_kps` 仍可参考快照（继续知识点）。

> 证据：详见 `2.OpenSpec design 决策/design-python-ai-tutoring-topic-mastery-signal.md`（§决策 3）｜ 语雀-决策记录.md D25
