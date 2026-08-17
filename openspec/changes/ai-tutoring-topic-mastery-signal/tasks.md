## 1. 模型契约改造（models/tutoring.py）

- [x] 1.1 `MasterySignalItem.kp_label` → `topic_label`（字段名 + description 语义改「题型」）
- [x] 1.2 确认 `question_kps`、`signal` 枚举、`mastery_snapshot` 入参不动

## 2. Prompt 改造（prompts.py）

- [x] 2.1 `_DECIDE_SYSTEM` JSON 示例：`kp_label` → `topic_label`
- [x] 2.2 `_DECIDE_SYSTEM` 掌握度信号段：输出题型（不是知识点），给「题型 vs 知识点」区分规则
- [x] 2.3 `_DECIDE_SYSTEM` 题型名稳定约束：用最常见、最短的题型名，别换说法 + few-shot 锚定
- [x] 2.4 `_DECIDE_SYSTEM` 移除「kp_label 优先复用快照候选」接地指令（mastery_snapshot 降级为背景参考）

## 3. 结构化纠错提示词（structured.py）

- [x] 3.1 `_schema_instructions` 字段名 `kp_label` → `topic_label`（**必须同步，防 Pydantic 校验失败 → 掌握度静默丢失**）

## 4. 测试（tests/tutoring/unit/）

- [x] 4.1 `test_models.py`：字段名断言 `kp_label` → `topic_label`（旧名拒绝）
- [x] 4.2 `test_structured.py`：`_schema_instructions` 断言含 topic_label、不含 kp_label
- [x] 4.3 `test_prompts.py`：新增「输出题型语义」「题型名稳定」「不接地 snapshot」「question_kps 仍知识点」prompt 断言

## 5. 验证

- [x] 5.1 全量单测 `pytest ai-edu-ai-service/tests/tutoring/unit/` 通过（含既有回归断言）
- [x] 5.2 real 用例人工验收：真实模型对鸡兔同笼题输出题型名「鸡兔同笼」而非「二元一次方程组」
