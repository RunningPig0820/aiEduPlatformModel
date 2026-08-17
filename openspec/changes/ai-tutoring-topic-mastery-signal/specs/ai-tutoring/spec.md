## MODIFIED Requirements

### Requirement: decide 评估学生回答

系统 SHALL 评估学生每轮回答,输出 `eval`(correct / error_type / emotion / exercise_complete)与 `mastery_signals`(topic_label + signal: mastered/practicing/struggling)。

掌握度信号主体是**题型**而非知识点:`topic_label` 输出题型名(如「鸡兔同笼」「相遇问题」「牛吃草」),**不输出**知识点名(如「二元一次方程组」「假设法」)——知识点掌握度由后端根据「题型掌握度 × 题型→知识点映射」派生。同一题型在不同学生/会话中 SHALL 输出一致的题型名,不随意换说法。`mastery_signals` 不再接地 `mastery_snapshot`(题型与知识点快照不同源)。

#### Scenario: 回答正确
- **WHEN** 学生回答正确且独立解出
- **THEN** `eval.correct=true`、`eval.exercise_complete=true`
- **THEN** `type=end` 且 `end_reason=COMPLETED`(联动约束)

#### Scenario: 回答错误
- **WHEN** 学生回答错误
- **THEN** `eval.correct=false`、`eval.error_type` 非空、`eval.emotion` 为 F7 七态之一
- **THEN** `mastery_signals` 反映薄弱信号(如 struggling),`topic_label` 为题型名
- **THEN** `type=hint` 或 `type=approach`(引导再想一步/给思路大纲),会话保持 ACTIVE,**不输出 `type=end`、不输出 `type=reveal`**

#### Scenario: 输出题型而非知识点
- **WHEN** 学生暴露某个题型的薄弱
- **THEN** `topic_label` 输出题型(如「鸡兔同笼」),**不输出**知识点(如「二元一次方程组」)

#### Scenario: 题型名稳定
- **WHEN** 学生在不同会话遇到同一题型
- **THEN** `topic_label` 输出一致的题型名(如「鸡兔同笼」而非「鸡兔同笼问题」)

#### Scenario: 情绪识别
- **WHEN** 学生表达困惑/沮丧等情绪
- **THEN** `eval.emotion` 返回 F7 七态之一(NEUTRAL/CONFUSED/FRUSTRATED/ANXIOUS/CONFIDENT/INTERESTED/BORED)
