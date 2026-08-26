# design-frontend-add-ai-tutoring-frontend

> summary: 讲AI辅导收尾总结卡片的渲染与按钮功能
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 10. 收尾总结卡片
> 模块: ai-tutoring ｜ 节: design-frontend-add-ai-tutoring-frontend
> 类别：业务流程

---

### 10. 收尾总结卡片

`done.status=ARCHIVED` 或 `archive` 响应含 `summary{knowledgePoints, weakPoints}` 与 `endReason`,渲染总结卡片:
- 涉及知识点(已掌握/练习中)、薄弱点、轮次、掌握度变化提示
- `[再来一题]` → 开新会话(`startSession`),清空当前线程
- `[回看对话]` 暂不做(transcript_url 留后续)
