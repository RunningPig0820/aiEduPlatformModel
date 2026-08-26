# design-backend-ai-tutoring

> summary: 讲AI答疑生成接口的请求响应规则
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: `POST /api/tutoring/generate`（流式 SSE，强模型）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-backend-ai-tutoring-POST-api-tutoring-generate流式-SSE强模型.md
> 类别：架构设计

---

### `POST /api/tutoring/generate`（流式 SSE，强模型）

请求：`{history, subject_hint, action_type(已放行), action_meta}`（含已放行的 type 约束）
响应：SSE 流式正文，与 action_type 一致（approach 只给思路、reveal 给完整答案等）。
