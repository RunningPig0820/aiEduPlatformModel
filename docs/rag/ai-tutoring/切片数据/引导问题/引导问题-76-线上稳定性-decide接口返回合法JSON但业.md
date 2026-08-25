# decide接口返回合法JSON，但业务字段值是非法业务枚举，你们做了几层校验？

> summary: 四层校验 + 确定性护栏，非法业务值不会放行成事故——模型格式不可信，代码做最后防线。
> 权威度: 1.0 ｜ 来源: 引导问题 ｜ 锚点: decide接口返回合法JSON，但业务字段值是非法业务枚举，你们做了几层校验？
> 模块: ai-tutoring ｜ 节: 线上稳定性
> 类别：线上稳定性

## 回答

**核心结论**：四层校验 + 确定性护栏，非法业务值不会放行成事故——模型格式不可信，代码做最后防线。

**分层展开**：
- **① Pydantic 模型校验**：ActionMeta.model_validate，闭集枚举（ActionType/EndReason/EmotionF7/MasterySignal）——非法枚举值直接校验失败。
- **② 归一化兜底**：emotion 中文/小写 → 大写枚举（"困惑/confused"→CONFUSED）——宽容模型常见错误，避免整条校验失败丢 mastery_signals。
- **③ 纠错重试**：校验失败发纠错消息只修 JSON 不整段重生成（重试域约束，多模态保持图片上下文）。
- **④ 段降级**：仍非法 → 下一段（function calling → JSON mode → 正则 → type=hint）。
- **业务联动护栏**：end_reason 非法/与 eval 矛盾 → end 联动护栏降级 concept（不恭喜、不泄解答）；safety_flag 异常 → 按 false 处理 + Java 侧安全终止兜底。
- **追问点**："非法 type 呢？" → 默认 HINT 放行（不阻断），degraded 标志监控——宁可降级也不卡会话。
