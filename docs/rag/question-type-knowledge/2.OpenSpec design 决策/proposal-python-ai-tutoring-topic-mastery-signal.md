## Why

后端把「掌握度主体」从知识点翻转为题型：学生掌握的是题型（「鸡兔同笼」），不是知识点（「二元一次方程组」）——学会鸡兔同笼 ≠ 掌握二元一次方程组。知识点掌握度改为由「题型掌握度 × 题型→知识点映射」在后端运行时派生，不再由 Python 直接输出知识点粒度。

当前 `mastery_signals[].kp_label` 是自由文本，题型/知识点混着出（`question_kps` 的 prompt 示例甚至把「鸡兔同笼」和「二元一次方程组」并列当知识点）。若继续输出知识点名，后端会把它当成一个题型落进题型掌握度表 → 题型库混入知识点名 → 掌握度、知识点派生覆盖度、图谱点亮整条链路数据都跟着脏。需要让 Python 端明确「我现在输出的是题型」，把整条链路粒度对齐。

## What Changes

- **掌握度信号语义翻转（必改）**：`mastery_signals` 输出**题型**（「鸡兔同笼」「相遇问题」「牛吃草」），不再输出知识点（「二元一次方程组」「假设法」）——知识点交给后端派生怕。
- **字段改名（加分项）**：`mastery_signals[].kp_label` → `topic_label`，语义从「知识点」改为「题型」。Java 已用 `@JsonAlias("topic_label")` 兼容旧名，改名无穿透风险。
- **题型名稳定规范**：同一题型在不同学生/会话输出一致的名字（「鸡兔同笼」不写成「鸡兔同笼问题」）。Java 只做字面归一化（全角半角/空白/去末尾语气词），不做同义词聚类，稳定性负担在 prompt 端。
- **`mastery_snapshot` 脱钩**：题型无法从知识点快照接地，`mastery_signals` 不再「优先复用快照候选」；`mastery_snapshot` 保留在请求里（Java 契约不动），仅作背景参考。
- **`question_kps` 不变**：继续输出知识点（读题列知识点，前端知识点分析数据源）。
- **`signal` 枚举不变**：mastered / practicing / struggling（对应后端 75/50/25）。

## Capabilities

### New Capabilities
<!-- 无：不新增能力，仅改 decide 的 mastery_signals 语义与字段名 -->

### Modified Capabilities
- `ai-tutoring`: `mastery_signals` 掌握度信号主体从知识点翻转为题型——字段名 `kp_label`→`topic_label`，输出内容为题型 label（知识点交给后端派生），题型名需稳定规范；`question_kps` 与 `signal` 枚举不变。

## Impact

- **`ai-edu-ai-service/models/tutoring.py`**：`MasterySignalItem.kp_label` → `topic_label`（字段名 + description 语义改题型）。
- **`ai-edu-ai-service/core/tutoring/prompts.py`**：`_DECIDE_SYSTEM` 掌握度信号段（输出题型、题型名稳定规范、不接地 snapshot）+ JSON 示例字段名同步。
- **`ai-edu-ai-service/core/tutoring/structured.py`**：`_schema_instructions` 纠错提示词字段名 `kp_label`→`topic_label`（**必须同步，否则 Pydantic 校验失败 → 掌握度静默丢失**）。
- **`ai-edu-ai-service/tests/tutoring/unit/`**：`test_models.py` / `test_structured.py` / `test_decider.py` / `test_prompts.py` 更新字段名与语义断言。
- **契约**：`ActionMeta.mastery_signals[].topic_label`（Java `@JsonAlias("topic_label")` 兼容旧名 `kp_label` 过渡）；`question_kps` / `signal` / `mastery_snapshot` 入参不变。
- **跨仓库**：前端读 Java 透传的 `kpLabel`（camelCase，与 Python 字段名无关），不受影响。
