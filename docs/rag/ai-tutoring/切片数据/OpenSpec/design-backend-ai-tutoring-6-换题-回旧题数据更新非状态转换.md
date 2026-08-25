# design-backend-ai-tutoring

> summary: 解决AI辅导后端换题回旧题的数据更新规则问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 6. 换题 / 回旧题（数据更新，非状态转换）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring

---

### 6. 换题 / 回旧题（数据更新，非状态转换）

```
学生贴新题 → decide 输出 switch + new_question
   → Java 仅 round_count/answer_request_count 归零（按新题重新计）
   → 旧题知识点不校正（留档，不点亮）
学生回旧题 → 又贴那道题 → decide 输出 switch 换回（或 concept）→ 同上
```

因为没有流程状态机，换题/回旧题只是**计数重置事件**；"当前题目"由 Python decide 每次从全量 history 推断，Java 不记录、不维护题目内容（记录易错：OCR 乱码、模型转述、陈旧快照）。学生怎么跳 agent 都能接住（它读全量历史判断）。
