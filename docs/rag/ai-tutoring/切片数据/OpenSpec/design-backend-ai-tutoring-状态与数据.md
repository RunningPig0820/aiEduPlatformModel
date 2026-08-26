# design-backend-ai-tutoring

> summary: 面试问AI答疑的状态数据归属，答明确各数据的存储归属
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 状态与数据
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> 类别：数据存储

---

## 状态与数据

| 概念 | 内容 | 归属 |
|------|------|------|
| 生命周期状态 | ACTIVE / ARCHIVED / TERMINATED | Java 会话表 |
| 护栏计数器 | round_count（≤20）、answer_request_count | Java 会话表（Redis 缓存） |
| 当前题目 | question_type/question_kind（MySQL）；**题目文本后端不记录**，Python 从 history 推断 | Java（MySQL）/ Python |
| 掌握度 | t_student_kp_mastery（按 URI） | Java（Python 经 action 上报 signal） |
| 错误事件 | t_tutoring_error_event | Java |
| 消息 | Redis（活跃期热存）→ COS（每轮实时整写，恒完整） | Java |
| 动作 | decide 输出的 type 闭集 | Python 决策 / Java 放行 |
