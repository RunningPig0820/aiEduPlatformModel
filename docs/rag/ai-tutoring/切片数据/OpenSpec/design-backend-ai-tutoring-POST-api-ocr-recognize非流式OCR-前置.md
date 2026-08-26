# design-backend-ai-tutoring

> summary: 讲OCR识别接口的请求响应与编排逻辑
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: `POST /api/ocr/recognize`（非流式，OCR 前置）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-backend-ai-tutoring-POST-api-ocr-recognize非流式OCR-前置.md
> 类别：操作流程

---

### `POST /api/ocr/recognize`（非流式，OCR 前置）

请求：`multipart file`（题目照片）
响应：`{text, confidence}`。Java 编排：前端上传 → Java 代理调此端点 → 返回识别文本供学生确认/修改 → 确认后作为**首条学生消息**进答疑。**不进 decide/generate 契约。**
