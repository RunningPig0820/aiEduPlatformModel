# 坑档案 J-QT7 掌握度信号字段改名脱节

> summary: 掌握度信号字段改名脱节：纠错提示词仍硬编码旧名
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J-QT7. 掌握度信号字段改名脱节
> 模块: question-analysis ｜ 节: 坑档案
> COS路径: rag-slices/question-analysis/坑档案/坑档案-J-QT7-掌握度信号字段改名脱节.md
> 类别：开发难点

---

**1. 问题现象**：掌握度信号静默丢失（mastery_signals 为空）。

**2. 触发流程**：`kp_label → topic_label` 改名 → `structured.py` 的 `_schema_instructions` 纠错提示词仍硬编码 `"kp_label"` → 模型输出旧名 → Pydantic 校验 topic_label 缺失 → 反复纠错失败 → 掉进兜底 fallback → 信号丢失。

**3. 根因分析**：function calling schema（绑定 Pydantic 模型，自动变 topic_label）与纠错提示词字段名**脱节**——模型按提示词输出 kp_label，schema 要 topic_label，永远校验不过。

**4. 排查过程**：改名后信号丢失，追到纠错提示词。

**5. 解决方案 & 改动点**：`_schema_instructions` 纠错提示词同步改为 `"topic_label"`；测试断言纠错提示词含 topic_label。（design-python-ai-tutoring-topic-mastery-signal Decision 2）

**6. 面试口述要点**：字段改名是个连环坑——Pydantic schema 会自动跟上新字段名，但纠错提示词里硬编码的旧名不会。模型按提示词输出旧名，schema 要新名，一直校验失败最后掉兜底，掌握度信号就静默丢了。改名必须连纠错提示词一起改。
