## ADDED Requirements

### Requirement: decide 输出题目涉及知识点

系统 SHALL 在 decide 输出的 ActionMeta 中携带 `question_kps`(可选字段,题目涉及知识点列表)。模型读题时顺手列出(如 "二元一次方程组"),**不额外调用、不改动决策逻辑**。字段为空(`null`)时前端显示占位"—"。该字段是前端「Agent 工作流」面板"知识点分析"阶段的数据源;后续独立的完整"读题知识点分析"功能可替换数据源(数据驱动,前端零改动)。

#### Scenario: 有值输出

- **WHEN** decide 收到含明确题目的请求,模型识别出涉及知识点
- **THEN** ActionMeta 携带 `question_kps` 非空列表(如 `["二元一次方程组"]`)

#### Scenario: 可空

- **WHEN** 模型未识别出明确知识点或换题短路(switch)
- **THEN** `question_kps` 为 `null` 或缺省,不产生错误

#### Scenario: 两条 function-calling 路径都透传

- **WHEN** 模型通过 function-calling(流式 `ark_stream` 或非流式 `structured`)或 content 兜底输出含 `question_kps` 的 ActionMeta JSON
- **THEN** 解析后的 ActionMeta 保留 `question_kps` 字段,不丢弃

### Requirement: decide 提示词声明 question_kps

系统 SHALL 在 decide 系统提示词(`_DECIDE_SYSTEM`)的输出格式中声明 `question_kps` 字段并给一句指令,指导模型读题时列出涉及知识点。

#### Scenario: 提示词包含字段

- **WHEN** 渲染 decide 提示词
- **THEN** 提示词文本含 `question_kps` 字段说明(含示例或"知识点"语义)

#### Scenario: 不干扰主决策

- **WHEN** 模型对"先想一步原则 / 动作闭集 / 首条消息规则"等主决策规则输出时
- **THEN** `question_kps` 为辅助可选字段,不要求每次必填,决策主流程行为不变
