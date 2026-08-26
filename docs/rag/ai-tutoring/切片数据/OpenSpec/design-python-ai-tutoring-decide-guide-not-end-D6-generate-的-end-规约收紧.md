# design-python-ai-tutoring-decide-guide-not-end

> summary: 收紧generate的end规约，禁止在end回复中写入完整解答
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D6. `generate` 的 `end` 规约收紧
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring-decide-guide-not-end
> 类别：开发难点

---

### D6. `generate` 的 `end` 规约收紧

`GENERATION_RULES["end"]` 改为：`end` 回复只说明原因/鼓励（COMPLETED=肯定掌握情况、ABANDONED=鼓励、ROUND_LIMIT=说明本轮结束），**禁止写入完整解答或最终数值**。堵住"结束语直接给答案"路径。
