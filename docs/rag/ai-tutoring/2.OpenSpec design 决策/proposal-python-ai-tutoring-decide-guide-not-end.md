## Why

学生作答（答错/答偏/跑题）时，decide 会误判为"内容与学习无关"→ 输出 `type=end`，会话被 Java 直接终止；且 end 的 `summary` 偶发直接给出完整答案。答错时偶发还会把"作答"误判成 `reveal`，Java 答案护栏拦一次后第二次放行完整答案并 `ANSWER_REVEALED` 收尾，打断引导链。根因：`_DECIDE_SYSTEM` 只有"完全无关→end / 过简模糊→concept"两档分类，缺"作答但答错→引导"这一档；`ai-tutoring` spec 的「回答错误」场景也只约束了 eval/mastery_signals、未约束 `type`。产品定位是苏格拉底式引导，答错应继续引导学生自己解，只有学生明确结束才结束。

此外，`完全无关 → end` 这一档同样过紧：学生闲聊、表达状态不佳（如"太热了 我不想问"）也会被判 `type=end` 被 Java 直接终止，即使学生并未主动表明结束。产品定位是会话尽量继续——无关内容应被"接住"并引导回题，只有学生**主动明确**表达结束/放弃才 `end(ABANDONED)`。

## What Changes

- **规则 1（两分法核心判定：是否在答题）**：decide 不做精细意图解读——无法确定学生每句话的确切意图（想结束/闲聊/抱怨状态），只判断与当前答题是否相关。**在答题**（作答/答错/答偏/求助/提问/追问，无论对错、是否跑偏）→ 引导解题（`hint` 只推一步 / `approach` 思路大纲），`eval.correct=false` 可填 `error_type`，会话 ACTIVE、绝不 `end`、绝不 `reveal`；**不在答题**（闲聊/状态表达如"太热了"/离题/纯打招呼/非数学/一切无法确定的话）→ 一律 `type=concept` 引导回题，保持 ACTIVE、绝不 `end`
- **规则 2（end 收紧三类 + 唯一例外）**：`type=end` 仅限 ①独立解出（COMPLETED）②学生表达结束的意思非常明确（ABANDONED，如"我不做了""结束""再见"）③安全；明确排除：在答题的内容、不在答题但未明确结束的内容绝不归 `end`
- **规则 3（终止不给答案）**：`GENERATION_RULES["end"]` 收紧——`end` 的 `summary` 只说明原因/鼓励，禁止写入完整解答或最终数值
- **规则 4（reveal 门禁收紧）**：仅当历史中学生**明确表达要答案**（"给答案""答案是多少"）才输出 `reveal`；答错、答偏绝不触发 `reveal`
- **规范补齐**：`ai-tutoring` spec「回答错误」场景补 `type` 约束、「区分无关与澄清」requirement 由两档升级为"是否在答题"两分法核心判定（在答题→引导 / 不在答题→concept 引导回题）
- **契约不变**：`ActionMeta` 无字段新增，Java↔Python 接口不变，仅行为收紧

## Capabilities

### New Capabilities
<!-- 无：不新增能力，仅收紧既有 decide 分类行为 -->

### Modified Capabilities
- `ai-tutoring`: decide 分类行为收紧——回答错误必须引导（hint/approach、保持 ACTIVE、绝不 end/reveal）、与学习无关的闲聊不再归 end 而是 concept 继续（保持 ACTIVE）、`end` 收紧为三类且 summary 不给答案、`reveal` 门禁收紧为仅明确要答案触发

## Impact

- **`ai-edu-ai-service/core/tutoring/prompts.py`**：`_DECIDE_SYSTEM`（新增"作答"档、无关→concept继续、end 收紧三类、reveal 门禁、补否定样例）+ `GENERATION_RULES["end"]`（终止不给答案）+ `GENERATION_RULES["concept"]`（接住闲聊、拉回题目）
- **`ai-edu-ai-service/tests/tutoring/unit/test_prompts.py`**：新增断言用例（答错→hint/approach 且 ACTIVE、明确放弃→end(ABANDONED)、不在答题→concept引导回题、答错绝不 reveal）；与既有 `test_end_vs_concept_distinction` 并列升级为两分法断言；`test_boundary.py` 无关/英语题断言 end→concept
- **契约**：`ActionMeta` schema 零变化；Java 护栏（轮次 20 / 答案计数）/ 前端均无需改动（已核实；无关消息 type 从 end 变 concept，前端按既有 concept 渲染）
- **风险**：prompt 多 section 联动，须防回归（首条默认 hint、换题 switch 短路、concept 澄清、exercise_complete→end、求助升 approach 均不受影响）
