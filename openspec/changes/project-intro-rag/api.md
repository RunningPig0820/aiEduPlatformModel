# RAG 项目介绍问答 API 接口文档

> 基础路径: `/api/rag`
>
> 更新日期: 2026-08-21
>
> 调用方: Java 后端（内部调用，需 `x-internal-token`）/ 前端 demo 页面

---

## 目录

- [通用响应结构](#通用响应结构)
- [1. 获取覆盖页面列表](#1-获取覆盖页面列表)
- [2. 页面概览卡](#2-页面概览卡)
- [3. 问答](#3-问答)
- [错误码说明](#错误码说明)
- [前端调用注意事项](#前端调用注意事项)

---

## 通用响应结构

所有接口均返回统一的 JSON 格式：

```json
{
  "code": "00000",
  "message": "success",
  "data": { ... }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | String | 状态码，`00000` 表示成功，其他为错误码 |
| message | String | 提示信息 |
| data | Object | 业务数据，可能为 null |

> 边界回答、无权限、降级属于**正常业务结果**，在 `data` 中以标志位返回，不是错误码。

---

## 1. 获取覆盖页面列表

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/rag/pages` |
| Content-Type | `application/json` |
| 需要鉴权 | 是（`x-internal-token`） |

### 响应参数

成功时 `data` 返回：

```json
{
  "pages": [
    { "id": "knowledge-graph", "name": "知识图谱", "permission": "public" },
    { "id": "ai-tutoring", "name": "AI答疑", "permission": "student" },
    { "id": "org-center", "name": "组织中心", "permission": "teacher" },
    { "id": "student-analysis", "name": "学生知识点分析", "permission": "student" },
    { "id": "rag-system", "name": "RAG问答系统", "permission": "public" }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| pages | Array | 覆盖的页面列表（含 RAG 系统自身作为功能点） |
| pages[].id | String | 页面标识（前端锚定传参用） |
| pages[].name | String | 页面展示名 |
| pages[].permission | String | 页面权限标签：`public`/`student`/`teacher`/`admin` |

### 请求示例

**cURL:**
```bash
curl -X GET http://localhost:8000/api/rag/pages \
  -H "x-internal-token: $INTERNAL_TOKEN"
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 10004 | 未登录 | token 无效或缺失 |

---

## 2. 页面概览卡

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/rag/page/overview` |
| Content-Type | `application/json` |
| 需要鉴权 | 是（`x-internal-token`） |

### 请求参数

**RequestBody**

```json
{
  "page": "ai-tutoring",
  "role": "student"
}
```

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| page | String | 是 | 必须是 `/api/rag/pages` 返回的 id | 当前点击的页面（页面锚定） |
| role | String | 是 | `student`/`teacher`/`admin` | demo 角色，`student` 为最高权限 |

### 响应参数

成功时 `data` 返回：

```json
{
  "page": "ai-tutoring",
  "name": "AI答疑",
  "permission": "student",
  "permission_ok": true,
  "overview": "AI答疑：苏格拉底式分步引导…（完善文档 §1 定位摘要）",
  "suggested_questions": [
    { "id": 1, "text": "你们为什么把答疑拆成三段服务？" },
    { "id": 2, "text": "怎么防止模型乱给答案？" },
    { "id": 3, "text": "这个页面的数据是怎么流转的？" }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| page | String | 页面 id |
| permission | String | 页面权限标签 |
| permission_ok | Boolean | 当前角色是否有权限（权限门前置校验结果） |
| overview | String | 页面一句话定位（完善文档 §1 摘要） |
| suggested_questions | Array | 引导问题 chips（**变体文案**，与索引层规范问题不同写法） |

### 请求示例

**cURL:**
```bash
curl -X POST http://localhost:8000/api/rag/page/overview \
  -H "Content-Type: application/json" \
  -H "x-internal-token: $INTERNAL_TOKEN" \
  -d '{"page": "ai-tutoring", "role": "student"}'
```

**JavaScript (fetch):**
```javascript
const response = await fetch('/api/rag/page/overview', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-internal-token': token
  },
  body: JSON.stringify({ page: 'ai-tutoring', role: 'student' })
});
const result = await response.json();
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 10001 | 参数错误 | page/role 缺失或非法 |
| 10004 | 未登录 | token 无效 |

---

## 3. 问答

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/rag/ask` |
| Content-Type | `application/json` |
| 需要鉴权 | 是（`x-internal-token`） |
| 支持流式 | 是（`stream=true` 时走 SSE，见下文） |

### 请求参数

**RequestBody**

```json
{
  "page": "ai-tutoring",
  "role": "student",
  "question": "你们为什么把答疑拆成三段服务？",
  "session_id": "sess-001",
  "stream": false
}
```

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| page | String | 否 | 覆盖页面 id | 页面锚定；缺省=全局模式（跨页检索） |
| role | String | 否 | `student`/`teacher`/`admin`，默认 `student` | demo 角色 |
| question | String | 是 | 非空，长度 ≤ 500 | 面试官问题 |
| session_id | String | 否 | 会话 id | 续接会话（页面锚定 + 追问计数） |
| stream | Boolean | 否 | 默认 false | true 时走 SSE 流式 |

### 响应参数（非流式）

成功时 `data` 返回：

```json
{
  "session_id": "sess-001",
  "turn": 2,
  "answer": "拆成三段是为了每个子任务独立可控…（AI答疑页§3）…",
  "citations": [
    { "page": "ai-tutoring", "section": "为什么这么设计", "source_doc": "…完善文档原文片段…" }
  ],
  "retrieved_docs": ["…召回文档原文面板…"],
  "mermaid": "graph TD; A[学生提问]-->B[意图分类]…",
  "boundary": false,
  "permission_denied": false,
  "degraded": false,
  "cost": {
    "prompt_tokens": 320,
    "completion_tokens": 140,
    "cumulative_tokens": 460,
    "cost_yuan": 0.003,
    "embedding_tokens": 0
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| session_id | String | 会话 id（无则新生成） |
| turn | Integer | 当前会话第几轮（页面锚定会话内） |
| answer | String | 生成答案（强制带引用，跨页按页标注） |
| citations | Array | 引用列表（页面+章节+源文档） |
| citations[].page | String | 来源页 |
| citations[].section | String | 来源章节 |
| citations[].source_doc | String | 源文档原文片段 |
| retrieved_docs | Array | 召回文档原文面板（本次检索命中的源文档段落） |
| mermaid | String\|null | 数据流图（命中数据流转类问题时返回 mermaid DSL） |
| boundary | Boolean | 是否边界回答（超范围，answer 为预写边界话术） |
| permission_denied | Boolean | 是否无权限拒绝（page 权限点不满足 role） |
| degraded | Boolean | 是否发生过降级（如 LLM 失败走预写答案/召回原文） |
| cost | Object | 成本明细（token 真算，流结束更新） |
| cost.prompt_tokens | Integer | 本轮输入 tokens |
| cost.completion_tokens | Integer | 本轮输出 tokens |
| cost.cumulative_tokens | Integer | 会话累计 tokens |
| cost.cost_yuan | Number | 累计费用（¥） |
| cost.embedding_tokens | Integer | embedding tokens（单列） |

### 流式响应（SSE，`stream=true`）

`Content-Type: text/event-stream`，事件序列：

| 事件 | data 内容 | 说明 |
|------|----------|------|
| `cost_update` | `{prompt_tokens, completion_tokens}` | 流开始时先给出已统计的输入 tokens |
| `citation` | `{page, section}` | 生成过程中逐条标注引用 |
| `content_delta` | `{text}` | 生成内容增量 |
| `boundary` | `{message}` | 边界回答（超范围，随后 `done`） |
| `permission_denied` | `{message}` | 无权限拒绝 |
| `done` | 完整 `data`（同非流式响应结构，含 `cost`） | 流结束，携带最终 usage 更新成本 |

### 请求示例

**cURL（非流式）:**
```bash
curl -X POST http://localhost:8000/api/rag/ask \
  -H "Content-Type: application/json" \
  -H "x-internal-token: $INTERNAL_TOKEN" \
  -d '{"page": "ai-tutoring", "role": "student", "question": "你们为什么把答疑拆成三段服务？", "stream": false}'
```

**JavaScript (fetch，流式):**
```javascript
const response = await fetch('/api/rag/ask', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-internal-token': token
  },
  body: JSON.stringify({ page: 'ai-tutoring', question: '这个页面的数据怎么流转？', stream: true })
});
const reader = response.body.getReader();
const decoder = new TextDecoder();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const lines = decoder.decode(value).split('\n');
  for (const line of lines) {
    if (line.startsWith('data:')) {
      // 解析事件，按 event 类型渲染 answer/citation/mermaid/cost
    }
  }
}
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 10000 | 系统错误 | 内部异常 |
| 10001 | 参数错误 | question 缺失/超长 |
| 10004 | 未登录 | token 无效 |

---

## 错误码说明

### 通用错误码 (1xxxx)

| code | message | 说明 |
|------|---------|------|
| 00000 | success | 成功 |
| 10000 | 系统错误 | 服务器内部错误 |
| 10001 | 参数错误 | 请求参数格式不正确 |
| 10004 | 未登录 | `x-internal-token` 缺失或无效 |

> 本模块无专用错误码：边界回答 / 无权限 / 降级均为正常业务结果（`data.boundary` / `data.permission_denied` / `data.degraded` 标志位）。

---

## 前端调用注意事项

### 1. 认证

内部调用须携带 `x-internal-token` 头（与现有 `/api/tutoring/vector/*` 一致）：

```javascript
const token = localStorage.getItem('internalToken');
fetch('/api/rag/ask', {
  headers: { 'Content-Type': 'application/json', 'x-internal-token': token }
});
```

### 2. 页面锚定（关键）

- 前端点击某个页面时，须将该页 id 通过 `/api/rag/page/overview` 传入，获得概览卡 + 引导问题。
- 后续问答**默认携带该 `page`**（页面模式锁页）；只有用户表达跨页问题或未点页时走全局模式（不传 `page`）。

### 3. 引导问题 = 变体文案

- 前端展示的 `suggested_questions` 与索引层规范问题**不同写法**（语义相同、字面不同），点击后仍走完整检索管道——前端不要做"问题 ID 直连答案"。

### 4. 会话与追问限制

- 前端把 `session_id` 回传以续接会话；达到 5 轮后服务端返回预写提示（非错误码），前端应引导用户开启新会话。

### 5. 成本展示

- 非流式直接读 `data.cost`；流式在 `done` 事件取最终 `cost`（usage 在流结束才返回）。

---

*文档生成时间: 2026-08-21*
