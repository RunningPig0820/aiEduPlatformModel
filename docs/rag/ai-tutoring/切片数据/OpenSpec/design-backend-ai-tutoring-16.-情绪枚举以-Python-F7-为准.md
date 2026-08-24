# design-backend-ai-tutoring

> summary: 面试问情绪枚举标准，答以Python F7七态为准
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 16. 情绪枚举以 Python F7 为准
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring

---

### 16. 情绪枚举以 Python F7 为准

**选择**: `eval.emotion` 使用 Python 侧权威的 **F7 七态**：`NEUTRAL / CONFUSED / FRUSTRATED / ANXIOUS / CONFIDENT / INTERESTED / BORED`。Java 学习域（答疑功能模块）定义 `TutoringEmotion` 值对象（7 态），`t_tutoring_error_event.emotion` / `t_tutoring_session.last_emotion` 存 F7 字符串。

**原因**: Python 是情绪输出方，枚举以输出方为准。**不强制复用** learning 域 `EmotionState`（5 态：POSITIVE/NEUTRAL/FRUSTRATED/CONFUSED/ANXIOUS）——那是情绪识别功能自己的枚举，两套并存，后续再统一。
