# design-backend-ai-tutoring

> summary: 解决AI辅导后端护栏规则的设计与实现问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 4. 护栏规则（Java，动作出口，确定性）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-backend-ai-tutoring-4-护栏规则Java动作出口确定性.md
> 类别：开发难点

---

### 4. 护栏规则（Java，动作出口，确定性）

| 护栏 | 判断 | 处理 |
|------|------|------|
| 答案 | `type=reveal` 且 `answer_request_count < 1` | 拒绝，重决策为 approach，count→1 |
| 轮次 | 引导类（hint/approach/evaluate 判定）且 `round_count ≥ 20` | 拒绝，强制 `end(ROUND_LIMIT)` |
| 安全 | 本地关键词命中（agent 启动前） | 终止，不启动 agent |
| 换题 | `type=switch` | 旧题知识点不校正（不点亮），仅计数重置（换题判定在 Python，后端不记录题目） |
| 收尾 | `type=end` | 按 end_reason 校正掌握度 + COS 终态写 + 置 ARCHIVED |
| 掌握度/错误 | action 带 `mastery_signals` / `eval.correct=false` | UPSERT 掌握度（label→URI）+ 写错误事件（含 emotion） |

护栏是**测试重点**（确定性规则，可单测），agent 路径不追求全覆盖测试。
