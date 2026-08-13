# AI 答疑 decide 行为收紧 测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证 `_DECIDE_SYSTEM` / `GENERATION_RULES`（`core/tutoring/prompts.py`）按规则收紧：①作答答错→引导不结束 ②无关（闲聊/日常表达）→concept 继续不终止 ③end 收紧三类 ④终止不给答案 ⑤reveal 门禁收紧；且不回归既有分类行为（首条 hint、换题 switch、concept 澄清、exercise_complete→end）。

### 1.2 测试方式
- **单元测试（主）**：`test_prompts.py` 文本断言——校验 prompt 是否包含规则措辞（正例 + 否定句）。因 LLM 分类无法确定性单测，文本断言保证**规则存在**。
- **real 用例（辅，可选）**：`tests/tutoring/real/` 实测 LLM 对典型输入的实际分类，人工验收模型**遵守**规则。
- **回归**：既有 `test_prompts.py` 断言（首条/换题/concept/exercise_complete）保持全绿。

### 1.3 测试环境配置
- pytest 配置：`ai-edu-ai-service/pytest.ini`
- 运行目录：`ai-edu-ai-service/tests/tutoring/unit/`
- real 用例需 `TUTORING_DECIDE_*` 环境变量（.env）与真实 LLM 凭证

---

## 2. 测试数据

| 输入 | 类型 | 期望行为 |
|-----|------|---------|
| "设鸡为x只"（作答，答错） | 作答-答错 | hint/approach，ACTIVE，不 end/reveal |
| "答案是x=5"（作答，答偏/错） | 作答-答偏 | hint/approach，ACTIVE，不 end/reveal |
| "我不做了 / 结束 / 再见" | 主动明确放弃 | end(ABANDONED) |
| "今天天气怎么样"（闲聊） | 无关 | concept（接住+引导回题，不终止） |
| "太热了 我不想问"（状态不佳） | 无关-日常表达 | concept（不终止；未主动表明结束） |
| "我会"但过程对一半 | 答对未解出 | approach 续推，不 end |
| "给我答案 / 答案是多少" | 明确要答案 | reveal（Java 审批放行与否） |

---

## 3. 测试用例清单

### 3.1 prompt 语义断言（test_prompts.py）

| 用例编号 | 场景描述 | 断言目标（prompt 措辞） | 对应 spec 场景 |
|---------|---------|---------|---------|
| PROMPT-001 | 作答→引导档存在 | 含"作答"档与"答错→hint/approach"、"eval.correct=false"、保持 ACTIVE 措辞 | 作答答错引导且保持活跃 |
| PROMPT-002 | 作答绝不 end/reveal | 含否定句"作答（无论对错/跑偏）绝不 end / 绝不 reveal" | 答错绝不 reveal / 作答不归无关 |
| PROMPT-003 | 无关→concept 继续 | 含"太热了/闲聊→concept"、保持 ACTIVE、绝不 end、"仅主动表明结束才 end" | 无关不归结束 / 闲聊输入 |
| PROMPT-004 | end 收紧三类 | end 仅 COMPLETED/ABANDONED/safety，明确排除"答错/答偏/求助/无关闲聊" | end 收紧三类 / 学生主动结束 |
| PROMPT-005 | reveal 门禁 | 仅"明确要答案"触发 reveal，"答错绝不触发" | 学生要答案（收紧） |
| PROMPT-006 | 答对未解出续推 | 含"答对但未独立解出→approach 续推（不给最终数值）" | 答对但未独立解出续推 |
| PROMPT-007 | generate end 不给答案 | `GENERATION_RULES["end"]` 含"禁止完整解答/最终数值" | generate 分类型约束(end) |

### 3.2 回归断言（既有 test_prompts.py 保持通过）

| 用例编号 | 场景描述 | 断言目标 |
|---------|---------|---------|
| PROMPT-101 | 首条消息默认 hint | 既有 `test_first_message_defaults_to_hint` 通过 |
| PROMPT-102 | 换题 switch 判定 | 既有 `test_current_question_inference_rule` 通过 |
| PROMPT-103 | concept 澄清不终止 | 既有 `test_end_vs_concept_distinction` 通过 |
| PROMPT-104 | exercise_complete→end | 既有 `test_exercise_complete_linkage` 通过 |
| PROMPT-105 | 先想一步原则 | 既有 `test_think_one_step_first_in_prompt` 通过 |

### 3.3 real 用例（可选，人工验收）

| 用例编号 | 场景描述 | 输入 | 预期结果 |
|---------|---------|------|---------|
| REAL-001 | 答错引导 | history 含题目 + "答案是x=5"(错) | decide 返回 hint/approach，非 end/reveal |
| REAL-002 | 主动明确放弃 | history 含题目 + "我不做了" | decide 返回 end(ABANDONED) |
| REAL-003 | 无关内容 | history 含题目 + "今天天气怎么样" | decide 返回 concept（非 end） |
| REAL-004 | 答错后要答案 | history 含题目 + "答案是多少" | decide 返回 reveal |

---

## 4. 错误码对照表

无新错误码。契约冻结（见 api.md），`403`（`x-internal-token`）/ `422`（Pydantic 校验）/ SSE `event: error` 沿用既有约定，本变更不涉及。

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| prompt 语义断言（新增） | 7 |
| 回归断言（既有保持通过） | 5 |
| real 用例（可选） | 4 |
| **总计（新增必做）** | **7** |

---

## 6. 测试执行顺序

```
test_prompts.py   : prompt 语义断言 + 回归（先跑，保证措辞不冲突）
test_decider.py   : 决策器机制（不受本变更影响，回归验证）
real/             : 可选，人工验收
```

---

## 7. 辅助方法

沿用 `test_prompts.py` 既有模式：`build_decide_prompt` / `build_decide_messages` / `GENERATION_RULES` 构造，断言 prompt 文本含关键措辞。real 用例复用 `tests/tutoring/real/test_tutoring_real.py` 的连接与请求构造方式。

---

## 8. 运行测试

```bash
# 单元测试（本变更核心）
pytest ai-edu-ai-service/tests/tutoring/unit/test_prompts.py -v

# 全量答疑单测（含回归）
pytest ai-edu-ai-service/tests/tutoring/unit/ -v

# 全量测试
pytest ai-edu-ai-service/tests/
```
