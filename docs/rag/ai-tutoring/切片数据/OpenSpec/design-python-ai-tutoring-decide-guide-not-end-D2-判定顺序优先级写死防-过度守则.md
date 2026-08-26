# design-python-ai-tutoring-decide-guide-not-end

> summary: 确定Python decide的判定优先级顺序
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D2. 判定顺序（优先级写死，防"过度守则"）
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring-decide-guide-not-end
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-python-ai-tutoring-decide-guide-not-end-D2-判定顺序优先级写死防-过度守则.md
> 类别：开发难点

---

### D2. 判定顺序（优先级写死，防"过度守则"）

```
safety_flag 命中 → 最高优先（Java 拦截）
is_new_question=true（Java 换题信号）→ 短路 switch
首条消息（history 仅 1 条、无老师回复）→ 默认 hint（仅明确求助可 approach）
在答题（作答/答错/答偏/求助/提问/追问，无论对错）→ hint/approach（绝不 end、绝不 reveal）
不在答题（闲聊/状态表达/离题/纯打招呼/非数学/无法确定）→ concept 引导回题（绝不 end）
唯一例外：学生表达结束的意思非常明确（"我不做了""结束""再见"）→ end(ABANDONED)
```

顺序写进 prompt，避免模型把"作答/闲聊/状态表达"误判成 end（会话被误终止）或把作答判成 reveal。
