## ADDED Requirements

### Requirement: decide 作答必须引导不结束

系统 SHALL 将学生**任何作答**（无论对错、是否跑偏/跑题）视为"在解答题目"，不属于"无关内容"。作答但答错/答偏时，decide 输出 `type=hint`（只推一步）或 `type=approach`（学生明确卡住/求助时给思路大纲），`eval.correct=false` 可填 `error_type`；会话**保持 ACTIVE**，绝不输出 `type=end`、绝不输出 `type=reveal`。

#### Scenario: 作答答错引导且保持活跃
- **WHEN** 学生作答但答案错误
- **THEN** decide 输出 `type=hint` 或 `type=approach`，`eval.correct=false`
- **THEN** 会话保持 ACTIVE，**不输出 `type=end`**（不被终止）

#### Scenario: 作答跑题仍引导
- **WHEN** 学生作答但答偏/跑题（内容属于解题尝试但不在答案上）
- **THEN** decide 输出 `type=hint` 或 `type=approach` 引导学生回到正题
- **THEN** 会话保持 ACTIVE，**不输出 `type=end`**

#### Scenario: 答错绝不 reveal
- **WHEN** 学生作答但答案错误，且未明确表达要答案
- **THEN** decide 绝不输出 `type=reveal`（不被 Java 放行完整答案）

#### Scenario: 答对但未独立解出续推
- **WHEN** 学生作答正确但未独立解出（`exercise_complete=false`）
- **THEN** decide 输出 `type=approach` 续推思路（不给最终数值），**不输出 `type=end`**

## MODIFIED Requirements

### Requirement: decide 输出动作元数据

系统 SHALL 通过 `POST /api/tutoring/decide`(非流式)接收对话上下文,输出动作元数据 ActionMeta。`type` 必须是闭集:hint / approach / reveal / concept / switch / end。`eval` 是软信号,`type` 是硬信号(Java 据此放行/拒绝)。

#### Scenario: 正常决策
- **WHEN** 收到带历史、轮次计数、当前题目、掌握度快照、subject=math 的 decide 请求
- **THEN** 返回 ActionMeta(含 `type`、`eval`、`mastery_signals`、`safety_flag` 等字段)
- **THEN** `type` 属于闭集枚举,不出现闭集外的值

#### Scenario: 学生要答案
- **WHEN** 学生消息**明确**表达要答案(如"给答案""答案是多少")
- **THEN** decide 输出 `type=reveal`(放行与否由 Java 护栏决定,Python 不做审批)
- **WHEN** 学生只是作答(含答错/答偏)而未明确要答案
- **THEN** decide **不输出** `type=reveal`

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
- **THEN** `type=hint` 或 `type=approach`(引导再想一步/给思路大纲),会话保持 ACTIVE,**不输出 `type=end`、不输出 `type=reveal`**

#### Scenario: 情绪识别
- **WHEN** 学生表达困惑/沮丧等情绪
- **THEN** `eval.emotion` 返回 F7 七态之一(NEUTRAL/CONFUSED/FRUSTRATED/ANXIOUS/CONFIDENT/INTERESTED/BORED)

### Requirement: decide 识别换题与收尾

系统 SHALL 识别学生中途换题(输出 `type=switch` + `new_question`)与收尾场景(输出 `type=end` + `end_reason`)。

#### Scenario: 中途换题
- **WHEN** 学生贴出新题
- **THEN** decide 输出 `type=switch` 且 `new_question` 为新题文本
- **THEN** 旧题历史视为已换题;当前题目由 Python 从 history 推断(最新学生消息为独立完整新题 → switch;答题/追问 → 保持当前题目)

#### Scenario: 学生主动结束
- **WHEN** 学生**明确**表达结束/放弃(如"我不做了""结束""算了""退出了")
- **THEN** decide 输出 `type=end` 且 `end_reason=ABANDONED`

#### Scenario: end 收紧三类
- **WHEN** 出现以下任一收尾场景:独立解出(COMPLETED)/ 学生**主动明确**放弃(ABANDONED)/ 安全内容(safety_flag)
- **THEN** decide 才输出 `type=end`,且按场景带相应 `end_reason`
- **WHEN** 学生只是作答(答错/答偏/求助)或表达与学习无关的闲聊/状态不佳(未主动表明结束)
- **THEN** decide **不输出** `type=end`

### Requirement: decide 以"是否在答题"判定学生消息

系统 SHALL 以两分法判定学生消息——decide 无法确定学生每句话的确切意图(想结束/闲聊/抱怨状态)，只判断与当前答题是否相关。**在答题**(作答/答错/答偏/求助/提问/追问，无论对错、是否跑偏)输出 `type=hint`/`approach` 引导解题，`eval.correct=false` 可填 `error_type`，**绝不输出 `type=end`、绝不输出 `type=reveal`**；**不在答题**(闲聊/状态表达如"太热了"/离题/纯打招呼/非数学/一切无法确定的话)输出 `type=concept` 正常回应、接住学生、引导回到当前题目，会话保持 ACTIVE、**不终止会话**。**唯一例外：学生表达结束的意思非常明确(如"我不做了""结束""再见")才输出 `type=end(ABANDONED)`**。

#### Scenario: 闲聊输入
- **WHEN** 学生发起"今天天气怎么样"等不在答题的内容
- **THEN** decide 输出 `type=concept`(接住+引导回题),会话保持 ACTIVE,**不输出 `type=end`**

#### Scenario: 非数学题目
- **WHEN** 学生提交一道英语题
- **THEN** decide 说明只辅导数学并引导回来,输出 `type=concept`,**不终止会话**

#### Scenario: 状态不佳不终止
- **WHEN** 学生表达状态不佳(如"太热了 我不想问")，结束意图无法确定
- **THEN** decide 默认引导回答题,输出 `type=concept`,**不输出 `type=end`**

#### Scenario: 纯打招呼不终止
- **WHEN** 学生消息只有问候(如"老师你好")
- **THEN** decide 输出 `type=concept` 回应并引导回题,**不输出 `type=end`**

#### Scenario: 作答不归结束
- **WHEN** 学生作答(答错/答偏/求助/提问/追问，无论对错)但未明确要答案、未明确要结束
- **THEN** decide 输出 `type=hint`/`approach` 引导,**不输出 `type=end`、不输出 `type=reveal`**

#### Scenario: 唯一例外结束
- **WHEN** 学生表达结束的意思非常明确(如"我不做了""结束""再见")
- **THEN** decide 输出 `type=end` 且 `end_reason=ABANDONED`

### Requirement: generate 按已放行类型生成正文

系统 SHALL 通过 `POST /api/tutoring/generate`(流式 SSE)接收已放行的 `action_type`,生成与类型一致的正文。

#### Scenario: 分类型约束
- **WHEN** `action_type=hint`
- **THEN** 生成只给 1 条提示/反问,零步骤,不含数值答案
- **WHEN** `action_type=approach`
- **THEN** 生成思路步骤大纲(步骤名+关键公式),不含完整演算、不含最终数值答案
- **WHEN** `action_type=reveal`
- **THEN** 生成完整解答与讲解(仅当 Java 已放行)
- **WHEN** `action_type=end`
- **THEN** 生成只说明原因/鼓励(COMPLETED=肯定掌握情况、ABANDONED=鼓励、ROUND_LIMIT=说明本轮结束),**禁止写入完整解答或最终数值**
