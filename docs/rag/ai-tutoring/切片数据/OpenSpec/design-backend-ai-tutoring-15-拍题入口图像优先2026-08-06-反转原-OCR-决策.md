# design-backend-ai-tutoring

> summary: 面试问拍题入口方案，答用视觉模型看图而非OCR
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 15. 拍题入口：图像优先（2026-08-06 反转原 OCR 决策）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring

---

### 15. 拍题入口：图像优先（2026-08-06 反转原 OCR 决策）

**选择（反转）**: 题目本身是图片（含受力分析图/实例图），答疑分析必须看到原图 → **不做传统 OCR 文本提取**，改用**视觉模型直接看图**。链路：前端 `POST /api/tutoring/sessions`（multipart 图片，可选 content）→ Java 认证 + 存 COS（`tutoring/questions/{studentId}/{sessionId}/{时间戳}.png`）→ 图片 URL 作为首条消息 `image_url` 进历史 → decide/generate 均携带 `image_url` 给**视觉模型**（豆包 `doubao-seed-2-0-lite`，全模态）看图作答。

**换题=学生发新图**: `POST /api/tutoring/sessions/{sessionId}/messages`（multipart 新图）→ **Java 检测新图 URL 首次出现** → decide 请求带 `is_new_question=true` → **Python 短路返回 `type=switch`（不调 LLM，确定性 100% 准）** → Java 重置轮次计数。判定权在 Java（只有 Java 知道"本轮新上传了图"），Python 无状态不依赖 history 图片结构推断（该做法有 bug：换题后每轮 history 都带旧图+新图，会被误判成连续换题）。

**原因（为什么不用传统 OCR）**: ① 数学公式/符号 OCR 质量是公认痛点，丢符号；② 受力分析图/实例图是图片本身的信息，文本提取必然有损，答疑分析必须引用原图；③ 视觉模型读图成本与 OCR 同数量级（~0.2–1 分/图），质量远优。**保留 `POST /api/tutoring/ocr` + `ai-edu.tutoring.ocr.enabled` 开关**作为兼容/降级路径（关闭时仅手打/粘贴，答疑核心不受阻）。
