# design-frontend-add-ai-tutoring-frontend

> summary: 讲AI答疑的请求答案、轮次计数及结束逻辑
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 6. 请求答案 + 轮次 + 结束
> 模块: ai-tutoring ｜ 节: design-frontend-add-ai-tutoring-frontend
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-frontend-add-ai-tutoring-frontend-6-请求答案-轮次-结束.md
> 类别：业务流程

---

### 6. 请求答案 + 轮次 + 结束

- 输入区右侧 `[请求答案]` 按钮,点击调 `requestAnswer`
- `answerRequestCount` 以 `meta.answerRequestCount`(服务端,后端已确认 SseMetaDTO 携带)为准,本地仅作未收到 meta 时的兜底;`meta.type=switch` 时归零
- 第 2 次点击(服务端计数 ≥1)→ **弹确认**:"获取完整答案后本次答疑将结束,确定?" → 确认后发送
- header 显示 `第 X/20 轮` 进度(roundCount 来自 meta/done 与服务端对账)
- `[结束答疑]` → 轻确认 → `archiveSession` → ended 视图
