# LLM Gateway API 接口文档

> 基础路径: `/api/llm`
>
> 服务端口: `9527`
>
> 更新日期: 2026-03-24

---

## 目录

- [认证说明](#认证说明)
- [1. 对话接口](#1-对话接口)
- [2. 流式对话接口](#2-流式对话接口)
- [3. 获取允许调用的模型列表](#3-获取允许调用的模型列表)
- [4. 获取所有模型列表](#4-获取所有模型列表)
- [5. 获取场景列表](#5-获取场景列表)
- [错误处理](#错误处理)

---

## 认证说明

所有接口需要在 Header 中携带内部 Token：

```
x-internal-token: my-secret-token-123
```

---

## 1. 对话接口

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/llm/chat` |
| Content-Type | `application/json` |

### 请求参数

**RequestBody**

```json
{
  "message": "请解释这个页面的功能",
  "user_id": 12345,
  "scene": "page_assistant",
  "provider": "zhipu",
  "model": "glm-4-flash",
  "session_id": "sess_abc123",
  "page_code": "homework_list",
  "context": {
    "page_meta": { "title": "作业列表" }
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| message | String | 是 | 用户消息内容，最大 10000 字符 |
| user_id | Long | 是 | 用户 ID |
| scene | String | 否 | 场景代码，用于自动选择模型 |
| provider | String | 否 | 指定 Provider，必须在白名单内 |
| model | String | 否 | 指定模型名称，需配合 provider |
| session_id | String | 否 | 会话 ID，用于多轮对话 |
| page_code | String | 否 | 当前页面编码 |
| context | Object | 否 | 额外上下文信息 |

**scene 可选值**:

| 值 | 说明 | 默认模型 |
|----|------|---------|
| page_assistant | 页面助手 | glm-4-flash (免费) |
| homework_grading | 作业批改 | deepseek-chat |
| faq | 常见问题 | glm-4-flash (免费) |
| image_analysis | 图片分析 | glm-4.6v |
| content_generation | 内容生成 | deepseek-chat |
| math_tutor | 数学辅导 | qwen-math-turbo |

**模型选择优先级**:
1. 如果指定了 `provider` + `model`，使用指定的模型（必须在白名单内）
2. 如果指定了 `scene`，根据场景自动选择模型
3. 否则使用默认模型 `zhipu/glm-4-flash`

### 响应参数

```json
{
  "response": "这个页面是作业列表页面...",
  "session_id": "sess_abc123",
  "model_used": "zhipu/glm-4-flash",
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 80,
    "total_tokens": 230
  },
  "tool_calls": []
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| response | String | AI 响应内容 |
| session_id | String | 会话 ID |
| model_used | String | 实际使用的模型，格式: `{provider}/{model}` |
| usage | Object | Token 使用量统计 |
| tool_calls | Array | 工具调用列表 |

### 请求示例

```bash
curl -X POST http://localhost:9527/api/llm/chat \
  -H "Content-Type: application/json" \
  -H "x-internal-token: my-secret-token-123" \
  -d '{
    "message": "你好",
    "user_id": 12345
  }'
```

```java
// Java 示例
HttpHeaders headers = new HttpHeaders();
headers.setContentType(MediaType.APPLICATION_JSON);
headers.set("x-internal-token", "my-secret-token-123");

Map<String, Object> body = new HashMap<>();
body.put("message", "你好");
body.put("user_id", userId);

HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
ResponseEntity<Map> response = restTemplate.postForEntity(
    "http://ai-service:9527/api/llm/chat",
    request,
    Map.class
);
```

---

## 2. 流式对话接口

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/llm/chat/stream` |
| Content-Type | `application/json` |
| 响应类型 | `text/event-stream` (SSE) |

### 请求参数

同 [对话接口](#1-对话接口)

### 响应格式 (SSE)

```
event: token
data: {"content": "你好"}

event: token
data: {"content": "！"}

event: done
data: {"model_used": "zhipu/glm-4-flash", "session_id": "xxx", "usage": {"total_tokens": 10}}

event: error
data: {"code": "400", "message": "错误信息"}
```

| event | 说明 |
|-------|------|
| token | 内容片段 |
| tool_call | 工具调用 |
| done | 流结束 |
| error | 错误 |

### 请求示例

```bash
curl -X POST http://localhost:9527/api/llm/chat/stream \
  -H "Content-Type: application/json" \
  -H "x-internal-token: my-secret-token-123" \
  -d '{"message": "你好", "user_id": 12345}'
```

---

## 3. 获取允许调用的模型列表

**重要**: 调用时只能使用此列表中的模型！

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/llm/allowed-models` |

### 响应示例

```json
{
  "code": "00000",
  "message": "success",
  "data": {
    "allowed_models": [
      {
        "provider": "zhipu",
        "model": "glm-4-flash",
        "full_name": "zhipu/glm-4-flash",
        "display_name": "GLM-4-Flash",
        "free": true,
        "supports_tools": true,
        "supports_vision": false,
        "description": "免费模型，适合大多数场景"
      },
      {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "full_name": "deepseek/deepseek-chat",
        "display_name": "DeepSeek Chat",
        "free": false,
        "supports_tools": true,
        "supports_vision": false,
        "description": "通用对话模型"
      }
    ],
    "default_model": "zhipu/glm-4-flash",
    "note": "调用时只能使用 allowed_models 中的模型"
  }
}
```

---

## 4. 获取所有模型列表

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/llm/models` |

### 响应示例

```json
{
  "code": "00000",
  "message": "success",
  "data": {
    "providers": [
      {
        "name": "zhipu",
        "display_name": "智谱 AI",
        "models": [...]
      }
    ]
  }
}
```

---

## 5. 获取场景列表

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/llm/scenes` |

### 响应示例

```json
{
  "code": "00000",
  "message": "success",
  "data": {
    "scenes": [
      {
        "code": "page_assistant",
        "default_provider": "zhipu",
        "default_model": "glm-4-flash",
        "description": "页面助手 - 解释当前页面内容"
      }
    ],
    "note": "scene 是可选的，可以直接指定 provider + model"
  }
}
```

---

## 错误处理

使用 HTTP 状态码表示错误：

| 状态码 | 说明 |
|--------|------|
| 400 | 参数错误或模型不允许调用 |
| 403 | 内部 Token 无效或缺失 |
| 500 | LLM 调用失败 |

**错误响应示例**:

```json
{
  "detail": "Model 'zhipu/glm-4.7' not allowed. Allowed models: ['zhipu/glm-4-flash', ...]"
}
```

---

## 调用架构

```
前端 ───JWT───▶ Java 后端 ───内部Token───▶ Python AI服务 (端口 9527)
```

**Java 后端职责**:
- 验证用户身份（JWT Token）
- 转发请求到 Python AI 服务
- 记录调用日志

**Python 服务职责**:
- 验证内部 Token
- 模型白名单校验
- 调用 LLM API
- 返回响应

---

## 在线文档

服务启动后访问：
- Swagger UI: http://localhost:9527/docs
- ReDoc: http://localhost:9527/redoc

---

*文档生成时间: 2026-03-24*