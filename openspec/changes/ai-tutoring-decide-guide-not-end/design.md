## Context

现状（已核实代码与规范）：
- `_DECIDE_SYSTEM`（`core/tutoring/prompts.py`）只有两档分类：**完全与学习无关 → `end`**、**过简/模糊但相关 → `concept`**。缺"作答但答错 → 引导"档，模型把"作答不属于题目答案"误归为"无关内容"→ 输出 `type=end`，Java `terminate()` 直接结束会话。
- `ai-tutoring` spec 的「回答错误」场景只约束了 `eval/mastery_signals`，**未约束 `type`**；「区分无关与澄清」requirement 是两档，规范层面同样缺"作答"档——prompt 只是忠实执行了规范里的两档。
- Java 侧零题目状态，无法语义区分"答错 vs 真无关"；`type=end` 且 `end_reason` 为空 → Java `terminate()`，终止回复正文 = `action.summary`。所以答错被误判为 end 后 Java 只能照单执行，**分类权必须在 Python decide**。
- 另一个 bug 源：答错时 decide 偶发输出 `reveal`（把答错误判为"学生要答案"）。Java 答案护栏拦首次（answer_request_count 0→1 降级 approach），但第二次 reveal 放行完整答案并 `ANSWER_REVEALED` 收尾，打断引导。

## Goals / Non-Goals

**Goals:**
- 学生任何作答（对/错/跑偏）都视为在解题：答错/答偏 → `hint`/`approach` + `eval.correct=false`，会话保持 ACTIVE，绝不 `end`、绝不 `reveal`
- 无关内容（闲聊/日常表达/非数学）→ `concept` 接住+引导回题，会话保持 ACTIVE、绝不 `end`；只有学生**主动明确**表达结束/放弃才 `end(ABANDONED)`
- `end` 收紧为三类（COMPLETED / ABANDONED / safety），且排除答错/答偏/求助/无关闲聊
- `end` 的 `summary` 只说明原因/鼓励，禁止完整解答或最终数值
- `reveal` 门禁收紧：仅学生**明确**表达要答案才触发
- 规范先行：`ai-tutoring` spec 补齐"作答"档与 type 约束，prompt 同步收紧
- 契约不变：`ActionMeta` 无字段新增，Java 护栏/前端零改动

**Non-Goals:**
- 不新增 ActionMeta 字段 / 不改变 Java↔Python 契约
- 不改 Java 护栏（轮次 20 上限、答案计数硬拦仍兜底）
- 不改换题短路（`is_new_question=true` → switch）
- 不做行为灰度开关（prompt 改动直接生效，回滚=还原文件）

## Decisions

### D1. Prompt 结构：两分法核心判定（是否在答题），不做精细意图解读

`_DECIDE_SYSTEM` 把分类简化为**是否在答题**的两分法——decide 无法确定学生每句话的确切意图（想结束/闲聊/抱怨状态），只判断与当前答题是否相关：

| 学生输入 | 判定 | 行为 |
|---|---|---|
| **在答题**（作答/答错/答偏/求助/提问/追问，无论对错） | 引导解题 | `hint`（只推一步）或 `approach`（卡住/求助给思路大纲），`eval.correct=false` 可填 `error_type`，会话 ACTIVE |
| **不在答题**（闲聊/状态表达/离题/纯打招呼/非数学/无法确定） | 引导回题 | `concept`（正常回应、接住学生、拉回题目），会话 ACTIVE，绝不 end |

**唯一例外**：学生表达结束的意思非常明确（"我不做了""结束""再见"）才 `end(ABANDONED)`。prompt 内保留否定硬规则："任何在答题的内容（无论对错、是否跑偏）绝不输出 `end`、绝不输出 `reveal`"——堵死"答错误终"与"答错误 reveal"两个 bug 源。

### D2. 判定顺序（优先级写死，防"过度守则"）

```
safety_flag 命中 → 最高优先（Java 拦截）
is_new_question=true（Java 换题信号）→ 短路 switch
首条消息（history 仅 1 条、无老师回复）→ 默认 hint（仅明确求助可 approach）
在答题（作答/答错/答偏/求助/提问/追问，无论对错）→ hint/approach（绝不 end、绝不 reveal）
不在答题（闲聊/状态表达/离题/纯打招呼/非数学/无法确定）→ concept 引导回题（绝不 end）
唯一例外：学生表达结束的意思非常明确（"我不做了""结束""再见"）→ end(ABANDONED)
```

顺序写进 prompt，避免模型把"作答/闲聊/状态表达"误判成 end（会话被误终止）或把作答判成 reveal。

### D3. hint vs approach 细分（沿用"先想一步原则"）

- 答错**默认 `hint`**（只推一步：先设哪个未知数、先看哪句条件）
- 学生**明确卡住/求助**（"我不会""太难了""给个思路"）→ `approach`（思路大纲）
- **答对但未独立解出**（`correct=true, exercise_complete=false`）→ `approach` 续推思路（不给最终数值），不 `end`

复用现有「先想一步原则：默认 hint，只有明确求助才 approach」段落，只需把"作答"档挂到该原则下。

### D4. `end` 收紧为三类 + `end_reason` 必填

| `end_reason` | 触发条件 |
|---|---|
| `COMPLETED` | 学生独立解出（`exercise_complete=true`） |
| `ABANDONED` | 学生**主动明确**表达放弃/结束（"我不做了""结束""再见"） |
| `safety_flag=true` | 高危内容，Java 拦截 |

明确排除：**答错、答偏、求助、与学习无关的闲聊绝不归 `end`**（无关走 `concept` 继续会话）。prompt 的 `end` 动作描述同步收紧。

### D5. `reveal` 门禁收紧

仅当**历史中学生明确表达要答案**（"给答案""答案是多少""直接说答案"）才输出 `reveal`；答错、答偏绝不触发。Java 答案护栏（首次 reveal 降级 approach、answer_request_count 计数）仍是兜底，Python 侧收紧是减少误触发、避免第二次 reveal 放行。

### D6. `generate` 的 `end` 规约收紧

`GENERATION_RULES["end"]` 改为：`end` 回复只说明原因/鼓励（COMPLETED=肯定掌握情况、ABANDONED=鼓励、ROUND_LIMIT=说明本轮结束），**禁止写入完整解答或最终数值**。堵住"结束语直接给答案"路径。

### D7. 测试策略

- **prompt 语义断言**（`test_prompts.py`，文本断言）：新增"作答→引导"档、无关→concept继续、end 收紧三类、reveal 门禁、end 不给答案四组断言；与既有 `test_end_vs_concept_distinction`/`test_first_message_defaults_to_hint`/`test_think_one_step_first_in_prompt` 并列
- **real 用例**（可选，`tests/tutoring/real/`）：实测 LLM 对"答错"输入的分类行为，人工验收
- 因 LLM 分类无法确定性单测，文本断言保证**规则存在**，real 用例保证**模型遵守**；Java 护栏兜底偶发

## Risks / Trade-offs

- **R1 [规则过多导致模型过度守则]** → 判定顺序（D2）写死 + 两分法各配典型正例；"在答题/不在答题"判定先于"唯一例外结束"，明确"作答与闲聊都不是结束"
- **R2 [答错后"要答案"被误禁]** → reveal 门禁以"历史中是否明确要答案"为准，不因答错而禁止；学生答错后明确要答案 → 合理走 reveal
- **R3 [LLM 分类不确定性，prompt 改了未必遵守]** → real 用例人工验收 + Java 护栏兜底（轮次 20 / 首次 reveal 降级 / answer_request_count）
- **R4 [prompt 联动回归]** → 既有 `test_prompts.py` 断言保持全绿（首条 hint、换题、concept、exercise_complete→end）+ 新增断言防新规则覆盖旧行为
- **R5 [无关→concept 的前端渲染]** → 无关消息 type 从 end 变 concept，前端按既有 concept 渲染（澄清气泡）而非终止会话；契约不变、零代码改动，但 UX 上"闲聊不再结束会话"，需在验收时确认前端对 concept 气泡与 ACTIVE 状态展示符合预期

## Migration Plan

1. 改 `_DECIDE_SYSTEM`（两分法 + 否定规则 + end 收紧 + reveal 门禁）与 `GENERATION_RULES["end"]`
2. 补 `test_prompts.py` 断言用例，跑全量单测（`pytest ai-edu-ai-service/tests/tutoring/unit/`）确认既有断言不回归
3. （可选）跑 real 用例人工验收 LLM 实际分类
4. 回滚：还原 `prompts.py` + 测试文件即可，无数据/契约残留

## Open Questions

- 无关内容（闲聊/非数学）是否走 Java terminate？—— **否**：无关不再输出 `end`，改 `concept` 继续会话（D4/D1），不回 Java `terminate()`
- 答对但未独立解出（`correct=true, exercise_complete=false`）的 `eval.error_type` 是否必填？—— 仅答错时填，答对续推可不填
