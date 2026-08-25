# design-backend-ai-tutoring

> summary: 解决AI辅导后端答案出口的Java硬拦机制问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 5. 答案出口机制（Java 硬拦）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring

---

### 5. 答案出口机制（Java 硬拦）

```
count=0 学生要答案 → decide 输出 reveal → Java 拦（count<1）→ 重决策 approach → count→1
count=1 学生再要答案 → decide 输出 reveal → Java 放行（count≥1）→ count→2，标记已揭示
```

`answer_request_count` 由 Java 管理；即使 agent 第一次就要输出 reveal，也会被 Java 硬拦成思路。"请求答案"识别由 decide 判断（学生在消息里要答案）；也可保留显式 `request-answer` API（见 api.md）。
