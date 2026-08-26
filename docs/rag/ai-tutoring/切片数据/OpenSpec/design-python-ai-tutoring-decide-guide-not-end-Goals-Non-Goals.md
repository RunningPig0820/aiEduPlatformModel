# design-python-ai-tutoring-decide-guide-not-end

> summary: 明确Python decide模块优化的目标与非目标
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Goals / Non-Goals
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring-decide-guide-not-end
> 类别：项目介绍

---

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
