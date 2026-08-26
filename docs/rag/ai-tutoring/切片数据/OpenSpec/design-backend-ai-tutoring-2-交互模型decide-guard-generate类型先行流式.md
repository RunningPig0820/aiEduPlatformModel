# design-backend-ai-tutoring

> summary: 答疑AI后端decide→guard→generate交互模型
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 2. 交互模型：decide → guard → generate（类型先行流式）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-backend-ai-tutoring-2-交互模型decide-guard-generate类型先行流式.md
> 类别：架构设计

---

### 2. 交互模型：decide → guard → generate（类型先行流式）

**选择**: 一次学生消息 = 两次 Python 调用，中间插 Java 护栏：

```
① Java 安全预检 → 组装上下文
② Python decide（非流式，快模型）→ 返回 action 元数据 {type, eval, mastery_signals, ...}
③ Java 护栏校验 action 元数据（见决策 4）
     ✗ 拒绝 → 让 Python 重决策（带 directive）或 Java 降级
     ✓ 通过 → 落库副作用（掌握度/错误/情绪/消息）
④ Python generate（流式 SSE，按已放行 type 生成正文）→ Java 透传前端
```

**原因**: "类型先行"保证**任何内容流入学生之前，type 已过护栏**——reveal 未授权时正文一个字都不会吐出去，护栏 100% 有效；同时 generate 流式保证体验流畅。decide 用快模型（非流式），generate 用强模型（流式）。
