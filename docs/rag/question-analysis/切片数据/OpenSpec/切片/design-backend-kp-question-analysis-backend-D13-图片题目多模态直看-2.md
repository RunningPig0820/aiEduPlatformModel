# 图片题目多模态直看（续）

> summary: 图片题多模态视觉模型直看（不经 OCR），独立 question-understand 端点模型写死视觉，非视觉风险隔离。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D13-图片题目多模态直看-2.md
> 类别：架构设计

---

### D13：图片题目多模态直看（Python 拍板方案 B）（续）

> 检索摘要：图片题多模态视觉模型直看（不经 OCR），独立 question-understand 端点模型写死视觉，非视觉风险隔离。

#### 方案选型与契约字段

- **为什么不经 `/api/llm/chat`（方案 A）**：不是所有模型都是视觉功能——通用 chat 路由到非视觉模型图就废了。方案 B 模型写死视觉 + 独立端点，非视觉风险天然隔离。
- **契约字段（snake_case，tutoring 域统一）**：请求 `image_url`/`topic_hint`/`grade`；响应 `topic_labels`/`question_kps`。Java `QuestionUnderstandRequest/Result` 已加 `@JsonProperty` 映射。
- **降级**：topic_labels 空 = 识别失败 → PENDING（与文本路径一致，不报错）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D13，下半）｜ 语雀-决策记录.md D23 ｜ 完善文档 02-题型分析主流程怎么走.md ｜ 坑档案 J-QT6
