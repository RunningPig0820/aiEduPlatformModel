# design-python-ai-tutoring

> summary: AI答疑decide输出的动作契约闭集规则
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 3. 动作契约(decide 输出,闭集)
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-ai-tutoring-3-动作契约decide-输出闭集.md
> 类别：架构设计

---

### 3. 动作契约(decide 输出,闭集)

```json
{
  "type": "hint" | "approach" | "reveal" | "concept" | "switch" | "end",
  "reason": "决策理由(可选,调试用)",
  "eval": {"correct": true, "error_type": null, "emotion": "NEUTRAL", "exercise_complete": false},
  "mastery_signals": [{"kp_label": "二元一次方程组", "signal": "practicing"}],
  "new_question": null,
  "end_reason": null,
  "summary": null,
  "safety_flag": false
}
```
- `type` 闭集,Java 决定放不放行;`eval` 是软信号(Java 放宽),`type` 是硬信号
- 新增可选 `reason` 字段(原 Java 契约没有,Python 侧加,供调试/评估)
