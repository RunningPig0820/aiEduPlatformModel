## 1. Prompt 改造（prompts.py）

- [x] 1.1 改造 `_DECIDE_SYSTEM`：把「终止型无关 vs 澄清型模糊」简化为两分法核心判定「是否在答题」（在答题→引导 / 不在答题→concept 引导回题），不做精细意图解读
- [x] 1.2 `_DECIDE_SYSTEM`：新增否定硬规则「作答（无论对错、是否跑偏）绝不输出 type=end、绝不输出 type=reveal」；`end` 收紧为三类（COMPLETED/ABANDONED/safety），明确排除答错/答偏/求助/无关闲聊
- [x] 1.3 `_DECIDE_SYSTEM`：无关（闲聊/日常表达/非数学）从 end 改 concept——正常回应、接住学生、引导回题，保持 ACTIVE、绝不 end；否定硬规则「无关 ≠ 结束，只有主动明确表达结束（"我不做了""结束""再见"）才 end(ABANDONED)」
- [x] 1.4 `_DECIDE_SYSTEM`：`reveal` 门禁收紧——仅历史中学生明确表达要答案（"给答案""答案是多少"）才输出，答错/答偏绝不触发
- [x] 1.5 `_DECIDE_SYSTEM`：把"作答"档挂到既有「先想一步原则」下（答错默认 hint 只推一步；明确卡住/求助才 approach；答对未独立解出→approach 续推）
- [x] 1.6 `GENERATION_RULES["end"]`：收紧为只说明原因/鼓励（COMPLETED/ABANDONED/ROUND_LIMIT 对齐），禁止写入完整解答或最终数值
- [x] 1.7 `GENERATION_RULES["concept"]`：涵盖接住无关闲聊（澄清模糊输入/回应闲聊 + 拉回当前题目）

## 2. 测试（test_prompts.py）

- [x] 2.1 新增「作答→引导」断言：prompt 含"作答/答错 → hint/approach"档、`eval.correct=false`、保持 ACTIVE、绝不 end/reveal 的否定措辞
- [x] 2.2 新增 `end` 收紧断言：end 三类 + 明确排除"答错/答偏/求助/无关闲聊"字样
- [x] 2.3 新增「无关→concept 继续」断言：prompt 含"太热了/闲聊→concept、保持 ACTIVE、绝不 end、仅主动表明结束才 end(ABANDONED)"
- [x] 2.4 新增 `reveal` 门禁断言：仅"明确要答案"触发 reveal，答错绝不触发
- [x] 2.5 新增 `GENERATION_RULES["end"]` 断言：end 规约不含"完整解答/最终数值"允许语义
- [x] 2.6 `test_boundary.py`：无关（"今天天气"/英语题）断言 end→concept（透传不终止）
- [x] 2.7 `test_tutoring_real.py`：闲聊断言由"end 终止"改为"不 end 继续"
- [x] 2.8 回归：既有 `test_end_vs_concept_distinction`/`test_first_message_defaults_to_hint`/`test_think_one_step_first_in_prompt` 等断言保持通过（措辞不冲突）

## 3. 验证

- [x] 3.1 跑全量单测：`pytest ai-edu-ai-service/tests/tutoring/unit/`，全部通过（含既有回归断言）
- [x] 3.2 real 用例人工验收：`test_unrelated_chatter_continues` 实测 LLM 对"今天天气怎么样"不再输出 end（真实模型已验证）
