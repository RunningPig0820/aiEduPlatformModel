# design-python-ai-tutoring

> summary: 面试问答中明确emotion定义归Python侧负责
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 8. emotion 归 Python 定义
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring

---

### 8. emotion 归 Python 定义

`EmotionF7` 七态:NEUTRAL/CONFUSED/FRUSTRATED/ANXIOUS/CONFIDENT/INTERESTED/BORED。Python 侧权威,Java 存储侧对齐。现有 `core/emotion_service.py` 是 stub,不建独立服务,折叠进 decide schema。
