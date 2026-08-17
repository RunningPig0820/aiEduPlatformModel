# /api/tutoring/question-understand 接口文档

> Java 内部通道（x-internal-token），供 `POST /api/kp/analyze-question/image` 调用。无会话、无观测。
>
> 字段沿用 tutoring 端点家族约定（snake_case，与 decide/generate 一致）。

## 请求

`POST /api/tutoring/question-understand`

```json
{
  "image_url": "https://cos-sign-...",
  "topic_hint": ["鸡兔同笼", "相遇问题"],
  "grade": 6
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| image_url | String | 是 | COS 签名 URL（Java 上传后传，Python 不接触原始图片） |
| topic_hint | Array[String] | 否 | 题型库 top-N 题型名（Java `findTopTopicLabels(20)`），收敛命名 |
| grade | Integer | 否 | 年级锚（本期不强用） |

## 响应

直接返回模型 JSON（同 `/api/llm/chat` 惯例，无 `code/message/data` 包装）：

```json
{
  "topic_labels": ["鸡兔同笼"],
  "question_kps": ["二元一次方程组"]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| topic_labels | Array[String] | 1~5 个题型名；空数组 = 识别失败（Java 降级 PENDING，不视为错误） |
| question_kps | Array[String] | 顺带识别的知识点名（可选，不强求） |

## 错误

- 缺 image_url / 未带 token → 4xx（参数校验，与 tutoring 端点一致）。
- 视觉调用失败 → HTTP 200 + 空 topic_labels（降级语义，不是错误）。

## 调用方（Java）

1. `POST /api/kp/analyze-question/image`（multipart file）→ 上传 COS → 得签名 URL。
2. 调本端点（带 topic_hint = 题型库 top-N）。
3. 拿到 topic_labels → 复用 resolve 管线（题型库命中/单点解析/PENDING）→ 组装 `QuestionAnalysisDTO`，与文本版一致。
