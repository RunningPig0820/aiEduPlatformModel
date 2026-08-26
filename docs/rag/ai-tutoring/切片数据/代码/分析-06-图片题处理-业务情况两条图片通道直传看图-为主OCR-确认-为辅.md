# 分析-06-图片题处理

> summary: 讲解图片题直传COS及多模态看图、OCR的业务逻辑
> 权威度: 0.8 ｜ 来源: 代码 ｜ 锚点: 业务情况（两条图片通道：直传看图 为主，OCR 确认 为辅）
> 模块: ai-tutoring ｜ 节: 分析-06-图片题处理
> COS路径: ai-tutoring/rag-slices/代码/分析-06-图片题处理-业务情况两条图片通道直传看图-为主OCR-确认-为辅.md
> 类别：操作流程

---

## 业务情况（两条图片通道：直传看图 为主，OCR 确认 为辅）

### 1. 图片直传 COS → 多模态看图（主通道）
- **前端**：`AiQa.jsx` 双入口——文件选择「直接传题」/ 粘贴图片 / 拖拽图片 → `sendWithImage` → `POST /sessions`(multipart) 或 `POST /sessions/{id}/messages`(multipart)。
- **Java**：`uploadQuestionImage` 图片上传 COS，按学生/会话/时间组织 `tutoring/questions/{studentId}/{sessionId}/{yyyyMMdd-HHmmss-SSS}.ext`；图片作为消息的 `image_url` 进 history（图片消息 content 可为空）。
- **Python**：decide/generate 的 history 里带 image_url 的 user 消息 → 多模态 HumanMessage（text + image_url）→ 豆包 doubao-seed-2-0-mini 直接看图解题/判对。
- **换题信号**：Java 检测「新图 URL 首次出现在 history」→ 本轮置 `is_new_question=true` → Python 短路 `type=switch`（见分析-01）。
- **图片格式白名单**：jpg/jpeg/png/webp/bmp（与 OCR 允许集一致），非白名单报 50006。

### 2. 视觉题目理解（独立端点，无会话）
- `POST /api/tutoring/question-understand`：一请求一返回 JSON，**模型写死 doubao 全模态**。
- 看图 → 1~5 个题型名（去编号/bullet 拆行）+ 顺带知识点；视觉失败 → 空 `topic_labels`（Java 降级 PENDING，不视为错误）。
- 慢修复：**关思考 + 20s 内部超时 + 关 SDK 重试**——doubao mini 默认开思考=先写草稿再答，实测开思考 50~145s、关思考看图 1.2s，是「图片分析慢」的根源修复。
- 前端 `analyzeQuestionImage` 走 `POST /kp/analyze-question/image`（60s 超时）复用该通道。

### 3. OCR 识别（辅助/兼容通道，开关控制）
- `POST /api/tutoring/ocr`（multipart）：图片 → Python `/api/ocr/recognize` → `{text, confidence}`，识别结果**必须经学生确认/修改**后再作为首条消息进答疑（OcrConfirmModal）。
- **`ocr.enabled` 开关**（`GET /api/tutoring/config` 下发前端）：关闭时前端隐藏拍照入口，仅手打/粘贴；开启时保留 OCR 前置。
- 用途定位：**截屏/公式/手写题的兜底文本化**；看图直传仍是主通道（图像优先）。
- OCR 超时 30s（前端 `recognize` timeout 30000）；Python 调用失败且重试后仍失败 → 50005。

### 4. 双通道关系（代码注释明示）
- 「图像优先：题目图片直传 COS → 多模态模型看图答疑；OCR 保留为兼容/降级通道」——OCR 不是主路径，是图片不可靠时的备选。

---
