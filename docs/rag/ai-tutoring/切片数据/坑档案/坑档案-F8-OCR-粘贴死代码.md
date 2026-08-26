# 坑档案

> summary: 解决OCR粘贴死代码的冗余流程问题
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: F8. OCR 粘贴死代码
> 模块: ai-tutoring ｜ 节: 坑档案
> 类别：开发难点

---

### F8. OCR 粘贴死代码
**1. 问题现象**：粘贴图片走 OCR 确认流程冗余——学生粘贴图还得 OCR 识别 + 人工确认，才能进答疑。

**2. 触发流程**（旧逻辑）：`AiQa.jsx` 根容器 `onPaste={ocr.handlePaste}` / `onDrop={ocr.handleDrop}` → 走 `useOcr.handleFile` → `tutoringApi.recognize`（OCR）→ `OcrConfirmModal` 确认 → `send(text)`。粘贴/拖拽图片必须先 OCR 识别 + 人工确认。且 `useOcr.js` 旧代码还有「剪贴板/拖拽文件无合法后缀 → 按 MIME 补后缀」的 `normalizeImageFile` 逻辑，只服务于 OCR 上传。

**3. 根因分析**：粘贴/拖拽图片本可直接走多模态看图（`sendWithImage` 上传原图），OCR 识别 + 确认弹窗对直接传图是多余步骤；`useOcr` 里的 `handlePaste`/`handleDrop`/`normalizeImageFile` 成为死代码。

**4. 排查过程**：从"粘贴图流程繁琐"反推 → 看粘贴/拖拽走 OCR 链路 → 对比多模态看图（sendWithImage）能力已具备 → 确认 OCR 前置冗余。

**5. 解决方案 & 改动点**：提交 `111cf01`：
- 粘贴/拖拽图片直接 `sendWithImage(file)`（多模态看图，不经 OCR）；文字粘贴放行
- `AiQa.jsx` 新增 `handlePaste`/改 `handleDrop`（`:120-133`、`:151-158`），容器绑定 `onPaste={handlePaste}` / `onDrop={handleDrop}`（`:165-169`）
- 删除 `useOcr.js` 中 `handlePaste`、`handleDrop`；`normalizeImageFile` 保留（仍供文件选择 OCR 用）。OCR 降级为兜底入口（Dropdown「拍照识别后确认」）

**6. 面试口述要点**：讲"**能力演进后要回头删旧链路**"——多模态看图上线后，OCR 前置 + 确认弹窗变成死流程。技术权衡：直接传图（多模态）替代 OCR 前置，OCR 降级兜底；删死代码防误导。踩坑收获：**新能力替代旧链路时，主动清理旧入口，别让两条路并存导致行为分歧**。

---
