# 06 图片题与 OCR

> 模块=ai-tutoring｜节=06｜问题表=操作｜权威度=高（正文）

## 为什么（语雀）

学生拍题是高频入口。数学题大量含**公式 + 图形**（受力分析图/实例图），传统 OCR 拆解必然丢信息。方案演进的核心认识：**答疑必须看到原图**。

## 怎么设计（方案）

**（方案口径，已演进）** 早期方案设计"拍照 → OCR 识别题目文本 → 学生确认 → 进答疑"（OCR 主入口）。2026-08 反转决策为"**图像优先**"：不做传统 OCR 文本提取，用视觉模型直接看图。

## 落地真相（代码）——图像优先为主 + OCR 兼容双通道

### 主通道：图片直传 COS → 多模态 doubao 看图
```
前端 选图/粘贴/拖拽 → sendWithImage → POST /sessions(图片 multipart)
  → Java 上传 COS：tutoring/questions/{studentId}/{sessionId}/{时间戳}.ext
  → 图片 URL 作为消息 image_url 进 history
  → decide/generate 的多模态 HumanMessage(text+image_url) → doubao 直接看图解题/判对
```
- 图片格式白名单：jpg/jpeg/png/webp/bmp
- **换题 = 学生发新图**：Java 检测新图 URL 首次出现在 history → 本轮置 `is_new_question=true` → Python **短路返回 switch（不调 LLM）** → Java 重置计数。判定权在 Java（Python 无状态，区分不了"本轮刚换 vs 早几轮已换"）。

### 视觉题目理解（独立端点，无会话）
`POST /api/tutoring/question-understand`：看图 → 1~5 个题型名 + 顺带知识点；失败 → 空 `topic_labels`（Java 降级 PENDING，不视为错误）。前端 `analyzeQuestionImage` 走它做题型分析。

### 兼容通道：OCR 识别（辅助/降级，开关控制）
- `POST /api/tutoring/ocr`：图片 → Python recognize → `{text, confidence}`，结果**必须经学生确认/修改**再进答疑（OcrConfirmModal）
- **`ocr.enabled` 开关**：关闭时前端隐藏拍照入口（仅手打/粘贴），答疑核心不受阻
- 定位：截屏/公式/手写题的兜底文本化

### 速度怎么保证（追问答案）
- 全链路模型统一 doubao mini，**关思考 + 20s 超时 + 关 SDK 重试**：doubao mini 默认开思考=先写草稿再答，实测开思考 50~145s、**关思考看图 1.2s**——这是图片分析慢的根因修复（坑档案 P1）
- 前端图片分析超时放宽 60s（视觉最坏 ~60s）

## 证据引用

- 图片题处理细节：`3.代码/分析-06-图片题处理.md`
- 换题信号：`3.代码/分析-01` + `TutoringAppService.sendMessage`（272-295）
- 坑档案：`git/坑档案.md`（P1 图片慢 50-145s、F4 图片超时 30→60s）
- 方案 vs 代码：`OpenSpec-代码对账.md`（A1 决策 15、A2 决策 11/14）
