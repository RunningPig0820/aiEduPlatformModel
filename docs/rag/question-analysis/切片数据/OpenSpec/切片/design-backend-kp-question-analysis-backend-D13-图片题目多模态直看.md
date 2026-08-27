# 图片题目多模态直看

> summary: 图片题多模态视觉模型直看（不经 OCR），独立 question-understand 端点模型写死视觉，非视觉风险隔离。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D13-图片题目多模态直看.md
> 类别：架构设计

---

### D13：图片题目多模态直看（Python 拍板方案 B）

> 检索摘要：图片题多模态视觉模型直看（不经 OCR），独立 question-understand 端点模型写死视觉，非视觉风险隔离。

#### 方案总览

图片题目默认走**多模态视觉模型直接看图**（不经 OCR，OCR 仅前端失败兜底）。Python 已拍板方案 B：新增 stateless 端点 `POST /api/tutoring/question-understand`，**模型 Python 侧写死**（TUTORING_DECIDE_MODEL = `doubao-seed-2-0-mini-260428`，Java 不指定模型，模型是 Java 黑盒；方舟开通 ID 若不同，改 Python `question_understand.py` 一行，Java 无感）。

#### 调用链路

```
Java POST /api/kp/analyze-question/image (multipart)
  → 无会话上传 COS（tutoring/questions/{studentId}/analyze/{ts}.ext，无 sessionId 依赖）
  → generatePresignedUrl（Python 要签名 URL，getUrl 非签名不可用）
  → 传 topicHint=findTopTopicLabels(20)（视觉识别命名朝题型库收敛）
  → 调 Python /api/tutoring/question-understand { image_url, topic_hint, grade }
  → 返回 { topic_labels, question_kps }
  → ①题型库命中权威 → ②questionKps 顺带展示（镜像校验，不强求）→ ③PENDING 挂起
```

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D13）｜ 语雀-决策记录.md D23 ｜ 完善文档 02-题型分析主流程怎么走.md ｜ 坑档案 J-QT6
