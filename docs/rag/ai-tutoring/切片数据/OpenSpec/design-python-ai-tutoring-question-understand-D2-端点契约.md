# design-python-ai-tutoring-question-understand

> summary: 面试问答中AI辅导题理解的端点契约定义
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D2. 端点契约
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring-question-understand
> 类别：架构设计

---

### D2. 端点契约

`POST /api/tutoring/question-understand`（Java 内部，x-internal-token）：

**请求**
```json
{
  "imageUrl": "https://cos-sign-...",   // 必填，COS 签名 URL（Java 上传后传）
  "topicHint": ["鸡兔同笼", "相遇问题", "牛吃草", ...],  // 可选，Java 传题型库 top-N，收敛命名
  "grade": 6                             // 可选，年级锚（本期不强用）
}
```

**响应**
```json
{
  "topicLabels": ["鸡兔同笼"],           // 1~5 个，空数组 = 识别失败（Java 降级 PENDING）
  "questionKps": ["二元一次方程组"]       // 可选，顺带识别知识点
}
```

对齐：语义 = 后端 `QuestionUnderstandingPort.understand(questionText, grade)` 的图片形态；空 `topicLabels` ↔ understand 返回空列表 → Java 降级 PENDING，与文本路径一致。
