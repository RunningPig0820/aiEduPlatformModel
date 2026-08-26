# design-backend-ai-tutoring

> summary: 答疑AI后端decide输出的动作契约规则
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 3. 动作契约（decide 输出）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-backend-ai-tutoring-3-动作契约decide-输出.md
> 类别：架构设计

---

### 3. 动作契约（decide 输出）

```json
{
  "type": "hint" | "approach" | "reveal" | "concept" | "switch" | "end",
  "reason": "决策理由（Python 可选发送；Java Jackson 默认容忍未知字段 FAIL_ON_UNKNOWN_PROPERTIES=false，无需建模）",
  "eval": {
    "correct": true,
    "error_type": null,
    "emotion": "NEUTRAL",
    "exercise_complete": false
  },
  "mastery_signals": [{"kp_label": "二元一次方程组", "signal": "practicing"}],
  "new_question": null,
  "end_reason": null,
  "summary": null,
  "degraded": false
}
```
- `degraded`：结构化输出兜底时 Python 置 true（type 必为 hint），Java 按普通 hint 放行 + 记日志（监控用），**不使用 503**
- `reason`：纯调试字段，Java 不建模，容忍未知字段即可

- `hint` 引导 / `approach` 思路 / `reveal` 答案 / `concept` 概念讲解 / `switch` 换题 / `end` 收尾
- `type` 是**闭集**（能力受限）；agent 自决 type，Java 决定放不放行
- `generate` 的 prompt 会带上已放行的 type，约束生成正文与 type 一致（如 approach 只给思路，不给完整演算）
