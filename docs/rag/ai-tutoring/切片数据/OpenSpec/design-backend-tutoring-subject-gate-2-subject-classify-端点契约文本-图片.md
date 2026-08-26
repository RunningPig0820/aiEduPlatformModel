# design-backend-tutoring-subject-gate

> summary: 说明subject-classify端点的契约、入参出参与模型配置
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 2. subject-classify 端点契约（文本 + 图片）
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-subject-gate
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-backend-tutoring-subject-gate-2-subject-classify-端点契约文本-图片.md
> 类别：架构设计

---

### 2. subject-classify 端点契约（文本 + 图片）

```
POST /api/tutoring/subject-classify（Python stateless，Java 经桥调）
  请求：{ "content": string|null, "image_url": string|null }   // 至少一个非空
  响应：{ "subject": "math"|"physics"|"chemistry"|"biology"|"other" }
```

- **提示词学科无关**：只问"这道题属于哪个学科？"，不做任何学科解题；图片无法辨认 → `other`。
- **文本和图片都支持**：无图走纯文本 HumanMessage；有图走多模态（复用 decide 看图同路径，`HumanMessage([{text},{image_url}])`）。
- **模型统一**：`doubao-seed-2-0-mini-260428`，temp 0.3（与 decide/understand 同款）。
- **绝不抛异常**：失败 → 空结果 → Java 按 math 放行（宁可放过不漏拦，见 Risks）。
