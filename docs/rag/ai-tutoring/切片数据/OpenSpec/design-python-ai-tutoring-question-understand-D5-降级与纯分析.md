# design-python-ai-tutoring-question-understand

> summary: 面试问答中AI辅导题理解的降级规则说明
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D5. 降级与纯分析
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring-question-understand

---

### D5. 降级与纯分析

- 视觉调用失败 / 解析失败 → `{topicLabels: []}` → Java 降级 PENDING（带 candidates 或空态），不报错。
- 端点无状态、不写 obs（与 analyze 纯分析一致；学生确认才走 vote）。
