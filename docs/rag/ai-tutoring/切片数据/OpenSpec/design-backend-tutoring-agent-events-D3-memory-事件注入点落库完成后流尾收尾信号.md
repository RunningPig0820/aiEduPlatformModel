# design-backend-tutoring-agent-events

> summary: 明确memory事件的注入时机与作用
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D3. memory 事件注入点：落库完成后、流尾收尾信号
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-events

---

### D3. memory 事件注入点：落库完成后、流尾收尾信号

**选择**: memory 由 Java 发。真实落库（`applySideEffects` + `archiveTranscript`）发生在 `buildStream` 前；**memory 事件放流尾**（generate token 后、done 前）作为"本轮成果已记录"的收尾信号，视觉上"读取→思考→把关→生成→记忆"最顺。

**detail**: 汇总本轮 mastery 信号（如 "二元一次方程组 → 练习中"）；无信号时 detail=null。

**原因**: 视觉时序（tokens→memory→done）比真实落库时序（generate 前）更符合用户直觉；落库提前做，事件只是收尾展示。与模型端文档 §四 一致。
