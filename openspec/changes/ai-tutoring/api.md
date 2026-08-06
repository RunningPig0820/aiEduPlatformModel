# AI 答疑 Python Agent API 接口文档

> 基础路径: `/api/tutoring`
>
> 更新日期: 2026-08-03
> **本仓库端点均为 Java↔Python 内部调用**,前端统一走 Java 网关(见 Java 仓库 `openspec/changes/ai-tutoring/api.md`)。调用需携带 `x-internal-token`(复用 `verify_internal_token` 模式)。

---

## 目录

- [通用约定](#通用约定)
- [1. 决策 decide](#1-决策-decide)
- [2. 生成 generate](#2-生成-generate)
- [3. OCR 识别](#3-ocr-识别)
- [错误码说明](#错误码说明)
- [Java 调用注意事项](#java-调用注意事项)

---

## 通用约定

内部端点成功响应为原始数据(非 `{code,message,data}` 包装——那是 Java 网关对外层)。错误统一走 HTTP 状态码 + JSON detail。

| Header | 必填 | 说明 |
|--------|------|------|
| `x-internal-token` | 是 | 内部认证 token,与 `settings.INTERNAL_TOKEN` 比对,缺失/错误返回 403 |
| `Content-Type` | 是 | `application/json` |

---

## 1. 决策 decide

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/tutoring/decide` |
| Content-Type | `application/json` |
| 需要登录 | 否(内部 token) |

### 请求参数

```json
{
  "history": [
    {"role": "user", "content": "鸡兔同笼，共35头94脚，各几只？"},
    {"role": "ai", "content": "先找题目里的已知条件，你能列出来吗？"}
  ],
  "round_count": 3,
  "answer_request_count": 0,
  "mastery_snapshot": [
    {"kp_key": "http://edukg.org/knowledge/3.1/...", "label": "二元一次方程组", "mastery_level": 50}
  ],
  "subject_hint": "math"
}
```

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| history | Array[{role, content}] | 是 | role ∈ user/ai | 对话历史(Java 从 Redis 组装;题目文本作为首条 user 消息,Python 从 history 推断当前题目) |
| round_count | Integer | 是 | ≥0 | 轮次计数 |
| answer_request_count | Integer | 是 | ≥0 | 已请求答案次数 |
| mastery_snapshot | Array[{kp_key, label, mastery_level}] | 否 | — | 学生已有掌握度(label 候选,接地用) |
| subject_hint | String | 是 | 默认 "math" | 学科(本期恒为 math) |

### 响应参数

非流式,返回 ActionMeta:

```json
{
  "type": "hint",
  "reason": "学生已列方程，下一步给一条引导性反问",
  "eval": {"correct": true, "error_type": null, "emotion": "NEUTRAL", "exercise_complete": false},
  "mastery_signals": [{"kp_label": "二元一次方程组", "signal": "practicing"}],
  "new_question": null,
  "end_reason": null,
  "summary": null,
  "safety_flag": false
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| type | String | 闭集:hint / approach / reveal / concept / switch / end |
| reason | String | 决策理由(可选,调试用) |
| eval.correct | Boolean | 学生回答是否正确 |
| eval.error_type | String|null | 错误类型 |
| eval.emotion | String | F7 七态:NEUTRAL/CONFUSED/FRUSTRATED/ANXIOUS/CONFIDENT/INTERESTED/BORED |
| eval.exercise_complete | Boolean | 是否独立解出 |
| mastery_signals | Array[{kp_label, signal}] | signal ∈ mastered/practicing/struggling;label 接地 snapshot |
| new_question | String|null | switch 时的新题文本 |
| end_reason | String|null | COMPLETED/ANSWER_REVEALED/ABANDONED/ROUND_LIMIT |
| summary | String|null | 收尾总结 |
| safety_flag | Boolean | 高危内容标记(拦截由 Java 执行) |
| degraded | Boolean | 结构化输出兜底标记(四段管线全失败时 true,Java 监控降级频次) |

### 请求示例

**cURL:**
```bash
curl -X POST http://localhost:8000/api/tutoring/decide \
  -H "Content-Type: application/json" \
  -H "x-internal-token: YOUR_INTERNAL_TOKEN" \
  -d '{
    "history": [{"role":"user","content":"设鸡有x只，则兔有35-x只"}],
    "round_count": 2,
    "answer_request_count": 0,
    "mastery_snapshot": [],
    "subject_hint": "math"
  }'
```

**JavaScript (fetch):**
```javascript
const res = await fetch('http://localhost:8000/api/tutoring/decide', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-internal-token': process.env.INTERNAL_TOKEN
  },
  body: JSON.stringify({
    history: [{ role: 'user', content: '设鸡有x只，则兔有35-x只' }],
    round_count: 2,
    answer_request_count: 0,
    mastery_snapshot: [],
    subject_hint: 'math'
  })
});
const actionMeta = await res.json();
```

### 常见错误

| HTTP | detail | 说明 |
|------|--------|------|
| 403 | Missing/Invalid internal token | 内部 token 缺失或不匹配 |
| 422 | 参数校验失败 | history/round_count 等字段缺失或类型错 |
| 500 | decide 失败 | LLM 调用失败(Java 重试 1 次后仍失败 → 40004) |

---

## 2. 生成 generate

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/tutoring/generate` |
| Content-Type | `application/json` |
| 需要登录 | 否(内部 token) |

### 请求参数

```json
{
  "history": [...],
  "subject_hint": "math",
  "action_type": "approach",
  "action_meta": {"eval": {"correct": true, "emotion": "NEUTRAL"}}
}
```

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| history | Array[{role, content}] | 是 | — | 对话历史(题目文本在历史中) |
| subject_hint | String | 是 | 默认 "math" | 学科 |
| action_type | String | 是 | 闭集(Java 已放行) | 生成正文的类型约束 |
| action_meta | Object | 否 | — | Java 放行时附带的决策元数据 |

### 响应参数

SSE 流式(media type `text/event-stream`):

```
event: token, data: {"content": "思路：先设鸡为x、兔为y，"}
event: token, data: {"content": "根据头数列一个方程，根据脚数列第二个，联立求解。"}
event: done,  data: {"model_used": "deepseek/deepseek-v4-flash"}
```

失败时:

```
event: error, data: {"code": "500", "message": "生成失败"}
```

### 请求示例

**cURL:**
```bash
curl -X POST http://localhost:8000/api/tutoring/generate \
  -H "Content-Type: application/json" \
  -H "x-internal-token: YOUR_INTERNAL_TOKEN" \
  -N \
  -d '{"history":[{"role":"user","content":"鸡兔同笼，共35头94脚，各几只？"},{"role":"user","content":"我不会"}],"subject_hint":"math","action_type":"approach","action_meta":{}}'
```

**JavaScript (fetch + ReadableStream):**
```javascript
const res = await fetch('http://localhost:8000/api/tutoring/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'x-internal-token': process.env.INTERNAL_TOKEN },
  body: JSON.stringify({ history: [{ role: 'user', content: '鸡兔同笼，共35头94脚，各几只？' }], subject_hint: 'math', action_type: 'approach', action_meta: {} })
});
const reader = res.body.getReader();
// 解析 SSE: 按 "event: token" / "event: done" / "event: error" 分派
```

### 常见错误

| HTTP | detail | 说明 |
|------|--------|------|
| 403 | Missing/Invalid internal token | 内部 token 缺失或不匹配 |
| 422 | 参数校验失败 | action_type 非闭集等 |
| 500 | 生成失败(流中 event: error) | 流中断,Java 不可重试,提示重发 |

---

## 3. OCR 识别

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/ocr/recognize` |
| Content-Type | `multipart/form-data` |
| 需要登录 | 否(内部 token) |

### 请求参数

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| file | File | 是 | 图片(jpg/png) | 数学题目照片 |

### 响应参数

```json
{
  "text": "鸡兔同笼，共35头94脚，各几只？",
  "confidence": 0.92
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| text | String | 识别出的题目文本(供前端确认/修改) |
| confidence | Float | 识别置信度 |

### 请求示例

**cURL:**
```bash
curl -X POST http://localhost:8000/api/ocr/recognize \
  -H "x-internal-token: YOUR_INTERNAL_TOKEN" \
  -F "file=@/path/to/question.jpg"
```

### 常见错误

| HTTP | detail | 说明 |
|------|--------|------|
| 403 | Missing/Invalid internal token | 内部 token 缺失或不匹配 |
| 400 | 无效图片 | 非图片或读取失败 |
| 500 | OCR 调用失败 | 识别服务异常 |

---

## 错误码说明

### 内部端点错误码(HTTP 状态)

| HTTP | 说明 |
|------|------|
| 403 | 内部 token 缺失/不匹配(Java 侧视为不可达) |
| 422 | Pydantic 参数校验失败 |
| 500 | LLM / OCR 调用失败 |
| 503 | 降级中(结构化输出兜底 type=hint,Java 按 hint 放行) |

> 对外统一错误码(40001/40002/40003/40004 等)由 **Java 网关** 层映射,Python 内部端点不直接输出该套码。

---

## Java 调用注意事项

1. **调用链**:Java 每轮先 `decide`(非流式)→ 护栏审批 → 再 `generate`(流式)透传前端。**generate 不可重试**(流已透传)。
2. **类型先行**:Java 收到 decide 的 `type` 后必须先过护栏,再调 generate;护栏拒绝时改 type 或 Java 降级话术,不调 generate。
3. **内部 token**:复用 llm-gateway `internalToken` 模式,Java 调用携带 `x-internal-token`。
4. **decide 可重试 1 次**(纯函数);仍失败 → 对外 40004"网络波动",会话保持。
5. **OCR 结果先确认**:识别出的题目文本先给前端确认/修改,再作为对话历史**首条 user 消息**进答疑(Java 零题目状态,不传不维护;当前题目由 Python 从 history 推断,换题判定也在 Python,Java 只认 `type=switch` 重置计数)。
6. **掌握度接地**:`mastery_snapshot` 的 label 请随请求传入,Python 优先复用,减少 Java 侧 label→URI 解析噪声。

---

*文档生成时间: 2026-08-03*
