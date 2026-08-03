## ADDED Requirements

### Requirement: 学生可以拍照识别数学题目

系统 SHALL 支持学生上传题目照片,通过 OCR 识别为题目文本,供进入答疑流程。OCR 是答疑前的独立预处理步骤,输出为文本题目(即答疑上下文中的 `current_question`)。

#### Scenario: 拍照识别题目成功
- **WHEN** 学生上传一张数学题目照片
- **THEN** OCR 识别出题目文本并返回(含识别结果)
- **THEN** 识别出的文本供学生确认/修改后进入答疑

#### Scenario: OCR 识别质量差
- **WHEN** OCR 识别结果可能错误(公式/上下标易错)
- **THEN** 系统要求学生确认或修改识别出的题目文本,再进入答疑

### Requirement: decide 输出动作元数据

系统 SHALL 通过 `POST /api/tutoring/decide`(非流式)接收对话上下文,输出动作元数据 ActionMeta。`type` 必须是闭集:hint / approach / reveal / concept / switch / end。`eval` 是软信号,`type` 是硬信号(Java 据此放行/拒绝)。

#### Scenario: 正常决策
- **WHEN** 收到带历史、轮次计数、当前题目、掌握度快照、subject=math 的 decide 请求
- **THEN** 返回 ActionMeta(含 `type`、`eval`、`mastery_signals`、`safety_flag` 等字段)
- **THEN** `type` 属于闭集枚举,不出现闭集外的值

#### Scenario: 学生要答案
- **WHEN** 学生消息表达要答案
- **THEN** decide 如实输出 `type=reveal`(放行与否由 Java 护栏决定,Python 不做审批)

### Requirement: decide 评估学生回答

系统 SHALL 评估学生每轮回答,输出 `eval`(correct / error_type / emotion / exercise_complete)与 `mastery_signals`(kp_label + signal: mastered/practicing/struggling)。

#### Scenario: 回答正确
- **WHEN** 学生回答正确且独立解出
- **THEN** `eval.correct=true`、`eval.exercise_complete=true`
- **THEN** `type=end` 且 `end_reason=COMPLETED`(联动约束)

#### Scenario: 回答错误
- **WHEN** 学生回答错误
- **THEN** `eval.correct=false`、`eval.error_type` 非空、`eval.emotion` 为 F7 七态之一
- **THEN** `mastery_signals` 反映薄弱信号(如 struggling)

#### Scenario: 情绪识别
- **WHEN** 学生表达困惑/沮丧等情绪
- **THEN** `eval.emotion` 返回 F7 七态之一(NEUTRAL/CONFUSED/FRUSTRATED/ANXIOUS/CONFIDENT/INTERESTED/BORED)

### Requirement: decide 识别换题与收尾

系统 SHALL 识别学生中途换题(输出 `type=switch` + `new_question`)与收尾场景(输出 `type=end` + `end_reason`)。

#### Scenario: 中途换题
- **WHEN** 学生贴出新题
- **THEN** decide 输出 `type=switch` 且 `new_question` 为新题文本
- **THEN** 旧题历史视为已换题,`current_question` 是权威(历史中其他题目仅作参考)

#### Scenario: 学生主动结束
- **WHEN** 学生表达结束/放弃
- **THEN** decide 输出 `type=end` 及相应 `end_reason`(ABANDONED 等)

### Requirement: decide 区分无关与澄清

系统 SHALL 区分"该终止的无关"与"该澄清的模糊"。完全与学习无关(闲聊/非数学)输出 `type=end`(终止);过简/打招呼等模糊输入输出 `type=concept` 带澄清问题,**不终止会话**。

#### Scenario: 闲聊输入
- **WHEN** 学生发起"今天天气怎么样"等无关内容
- **THEN** decide 输出 `type=end`,供 Java 终止会话

#### Scenario: 非数学题目
- **WHEN** 学生提交一道英语题
- **THEN** decide 判定 subject≠math,输出 `type=end`(终止)

#### Scenario: 模糊输入不终止
- **WHEN** 学生消息过简(如"我不会"、"老师你好")
- **THEN** decide 输出 `type=concept` 带澄清引导,**不输出 `type=end` 终止会话**

### Requirement: generate 按已放行类型生成正文

系统 SHALL 通过 `POST /api/tutoring/generate`(流式 SSE)接收已放行的 `action_type`,生成与类型一致的正文。

#### Scenario: 分类型约束
- **WHEN** `action_type=hint`
- **THEN** 生成只给 1 条提示/反问,零步骤,不含数值答案
- **WHEN** `action_type=approach`
- **THEN** 生成思路步骤大纲(步骤名+关键公式),不含完整演算、不含最终数值答案
- **WHEN** `action_type=reveal`
- **THEN** 生成完整解答与讲解(仅当 Java 已放行)

### Requirement: 类型先行流式 SSE

系统 SHALL 按"类型先行"协议流式返回:先 `meta`(已放行 type)→ `token`(正文流)→ `done`(状态+eval)。护栏拒绝时不产生 `token` 流。

#### Scenario: 正常流式
- **WHEN** generate 收到已放行的 action_type
- **THEN** SSE 先发 `event: meta`(含 type),再发 `event: token`(正文流),最后 `event: done`

#### Scenario: 流中失败
- **WHEN** 生成过程中发生错误
- **THEN** 发出 `event: error`,流终止

### Requirement: 结构化输出保障

系统 SHALL 保证 decide 接口绝不返回畸形 ActionMeta。当结构化输出失败时逐级降级,最终兜底为 `type=hint`,并记录日志。

#### Scenario: 结构化输出失败
- **WHEN** function calling 输出失败
- **THEN** 尝试 JSON mode;仍失败则正则提取 + Pydantic 校验;再失败则兜底 `ActionMeta(type=hint)`
- **THEN** 返回的 ActionMeta 始终通过 Pydantic 校验

### Requirement: 掌握度信号接地

系统 SHALL 将 `mastery_signals.kp_label` 接地到 `mastery_snapshot` 中已有的知识点 label,优先复用候选,降低 Java 侧 label→URI 解析噪声。

#### Scenario: label 接地
- **WHEN** decide 请求的 `mastery_snapshot` 含已有 label(如"二元一次方程组")
- **THEN** 输出 `mastery_signals` 优先复用快照中的 label
- **THEN** 新推断的 label 提示与教材知识点名一致

### Requirement: 安全 flag 输出

系统 SHALL 在 decide 中检测高危内容(自伤/暴力等),输出 `safety_flag` 供 Java 判定。Python 只输出 flag,不做拦截。

#### Scenario: 高危内容
- **WHEN** 学生消息命中高危内容
- **THEN** decide 返回 `safety_flag=true`(拦截/终止由 Java 执行)
