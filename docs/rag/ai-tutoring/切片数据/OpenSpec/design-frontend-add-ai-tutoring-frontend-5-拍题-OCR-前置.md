# design-frontend-add-ai-tutoring-frontend

> summary: 讲AI答疑的拍题OCR前置交互流程
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 5. 拍题 OCR 前置
> 模块: ai-tutoring ｜ 节: design-frontend-add-ai-tutoring-frontend
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-frontend-add-ai-tutoring-frontend-5-拍题-OCR-前置.md
> 类别：操作流程

---

### 5. 拍题 OCR 前置

- 输入区 📷 按钮**常驻显示**(经讨论,OCR 基本不会关闭,不读配置;若后端关闭,调用返回错误码走通用提示)
- 点击 → 隐藏 `input[type=file] accept="image/*"`(移动端自动唤起相机/相册)
- 上传 `POST /api/tutoring/ocr` → 弹 `OcrConfirmModal`:识别文本置于可编辑 textarea + 置信度指示
- 确认 → 文本进入消息通道:
  - 无活跃会话 → 作为 `startSession(message)` 的首条消息
  - 已有活跃会话 → 作为 `sendMessage` 的内容(decide 自行判 switch)
- 取消/识别失败 → 关闭弹窗,toast 引导"请重新上传清晰照片"
- 识别结果**必须经学生确认**才进入答疑(后端契约要求)
