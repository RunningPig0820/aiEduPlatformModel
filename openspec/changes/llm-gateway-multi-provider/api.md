# LLM Gateway API 接口文档

> 基础路径: `/api/llm`
>
> 更新日期: 2025-03-20

---

## 目录

- [通用响应结构](#通用响应结构)
- [1. 对话接口](#1-对话接口)
- [2. 流式对话接口](#2-流式对话接口)
- [3. 获取可用模型列表](#3-获取可用模型列表)
- [错误码说明](#错误码说明)

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

---

## 1. 对话接口

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/llm/chat` |
| Content-Type | `application/json` |
| 需要登录 | 是（Java后端内部调用） |
| 认证方式 | 内部 Token (x-internal-token) |

### 请求参数

**RequestBody**

```json
{
  "message": "请解释这个页面的功能",
  "scene": "page_assistant",
  "session_id": "sess_abc123",
  "page_code": "homework_list",
  "user_id": 12345,
  "model_provider": "zhipu",
  "model_name": "glm-4-flash",
  "context": {
    "page_meta": { "title": "作业列表", "code": "homework_list" }
  }
}
```

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| message | String | 是 | 非空，最大 10000 字符 | 用户消息内容 |
| scene | String | 是 | 枚举值 | 场景代码，用于模型路由 |
| session_id | String | 否 | UUID 格式 | 会话ID，用于多轮对话 |
| page_code | String | 否 | 最大 64 字符 | 当前页面编码，用于上下文 |
| user_id | Long | 是 | 正整数 | 用户ID，由 Java 后端从 JWT 解析 |
| model_provider | String | 否 | 枚举值 | 指定 Provider，不传则自动路由 |
| model_name | String | 否 | 最大 64 字符 | 指定模型名称，需配合 model_provider |
| context | Object | 否 | - | 额外上下文信息 |

**scene 枚举值**:

| 值 | 说明 | 默认模型 |
|----|------|---------|
| page_assistant | 页面助手 | glm-4-flash (免费) |
| homework_grading | 作业批改 | deepseek-chat |
| faq | 常见问题 | glm-4-flash (免费) |
| image_analysis | 图片分析 | glm-4.6v |
| content_generation | 内容生成 | deepseek-chat |

### 响应参数

成功时 `data` 返回：

```json
{
  "response": "这个页面是作业列表页面，您可以在这里...",
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
| session_id | String | 会话ID，用于后续多轮对话 |
| model_used | String | 实际使用的模型，格式: `{provider}/{model}` |
| usage | Object | Token 使用量统计 |
| tool_calls | Array | 工具调用列表（如果有） |

**tool_calls 结构**（当 AI 决定调用工具时）:

```json
{
  "tool_calls": [
    {
      "id": "call_abc123",
      "name": "search_questions",
      "arguments": { "keyword": "数学", "limit": 5 }
    }
  ]
}
```

### 请求示例

**cURL:**
```bash
curl -X POST http://localhost:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -H "x-internal-token: your-internal-token" \
  -d '{
    "message": "请解释这个页面的功能",
    "scene": "page_assistant",
    "page_code": "homework_list",
    "user_id": 12345
  }'
```

**Java (RestTemplate):**
```java
HttpHeaders headers = new HttpHeaders();
headers.setContentType(MediaType.APPLICATION_JSON);
headers.set("x-internal-token", internalToken);

Map<String, Object> body = new HashMap<>();
body.put("message", "请解释这个页面的功能");
body.put("scene", "page_assistant");
body.put("page_code", "homework_list");
body.put("user_id", userId);  // Java 后端从 JWT 中解析

HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
ResponseEntity<Map> response = restTemplate.postForEntity(
    "http://ai-service:8000/api/llm/chat",
    request,
    Map.class
);
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 20001 | 模型不可用 | 指定的模型不存在或未配置 |
| 20002 | Provider 未注册 | 指定的 Provider 未实现 |
| 20003 | API 调用失败 | LLM 厂商 API 调用异常 |
| 20004 | 内容审核不通过 | 触发内容安全策略 |
| 20005 | 超出限流 | 请求频率超限 |

---

## 2. 流式对话接口

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/llm/chat/stream` |
| Content-Type | `application/json` |
| 响应类型 | `text/event-stream` (SSE) |
| 需要登录 | 是 |

### 请求参数

同 [对话接口](#1-对话接口)

### 响应格式

使用 Server-Sent Events (SSE) 返回流式数据：

```
event: token
data: {"content": "这个"}

event: token
data: {"content": "页面"}

event: token
data: {"content": "是..."}

event: done
data: {"model_used": "zhipu/glm-4-flash", "usage": {...}}
```

**事件类型**:

| event | 说明 | data 结构 |
|-------|------|-----------|
| token | 内容片段 | `{"content": "..."}` |
| tool_call | 工具调用 | `{"id": "...", "name": "...", "arguments": {...}}` |
| done | 流结束 | `{"model_used": "...", "usage": {...}}` |
| error | 错误 | `{"code": "...", "message": "..."}` |

### 请求示例

**Java (WebClient 流式处理):**
```java
WebClient webClient = WebClient.builder()
    .baseUrl("http://ai-service:8000")
    .defaultHeader("x-internal-token", internalToken)
    .build();

Flux<String> stream = webClient.post()
    .uri("/api/llm/chat/stream")
    .contentType(MediaType.APPLICATION_JSON)
    .bodyValue(Map.of(
        "message", "请解释这个页面",
        "scene", "page_assistant",
        "user_id", userId
    ))
    .retrieve()
    .bodyToFlux(String.class);

stream.subscribe(event -> {
    // 解析 SSE 事件，转发给前端
    System.out.println("Received: " + event);
});
```

**cURL:**
```bash
curl -X POST http://localhost:8000/api/llm/chat/stream \
  -H "Content-Type: application/json" \
  -H "x-internal-token: your-internal-token" \
  -d '{"message": "请解释这个页面", "scene": "page_assistant", "user_id": 12345}'
```

---

## 3. 获取可用模型列表

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/llm/models` |
| 需要登录 | 是 |

### 请求参数

无

### 响应参数

```json
{
  "code": "00000",
  "message": "success",
  "data": {
    "providers": [
      {
        "name": "zhipu",
        "display_name": "智谱AI",
        "models": [
          {
            "name": "glm-4-flash",
            "display_name": "GLM-4-Flash",
            "free": true,
            "supports_tools": true,
            "supports_vision": false
          },
          {
            "name": "glm-4.5-air",
            "display_name": "GLM-4.5-Air",
            "free": false,
            "supports_tools": true,
            "supports_vision": false
          },
          {
            "name": "glm-4.6v",
            "display_name": "GLM-4.6V",
            "free": false,
            "supports_tools": true,
            "supports_vision": true
          }
        ]
      },
      {
        "name": "deepseek",
        "display_name": "DeepSeek",
        "models": [
          {
            "name": "deepseek-chat",
            "display_name": "DeepSeek Chat",
            "free": false,
            "supports_tools": true
          }
        ]
      }
    ],
    "scene_defaults": {
      "page_assistant": {"provider": "zhipu", "model": "glm-4-flash"},
      "homework_grading": {"provider": "deepseek", "model": "deepseek-chat"}
    }
  }
}
```

---

## 错误码说明

### 通用错误码 (1xxxx)

| code | message | 说明 |
|------|---------|------|
| 00000 | success | 成功 |
| 10000 | 系统错误 | 服务器内部错误 |
| 10001 | 参数错误 | 请求参数格式不正确 |
| 10003 | 参数无效 | 参数校验失败 |
| 10004 | 未授权 | 内部 Token 无效 |

### LLM 模块错误码 (2xxxx)

| code | message | 说明 |
|------|---------|------|
| 20001 | 模型不可用 | 指定的模型不存在或未配置 API Key |
| 20002 | Provider 未注册 | 指定的 Provider 未实现 |
| 20003 | API 调用失败 | LLM 厂商 API 调用异常 |
| 20004 | 内容审核不通过 | 触发内容安全策略 |
| 20005 | 超出限流 | 请求频率超限 |
| 20006 | Token 超限 | 上下文长度超限 |

---

## 前端调用注意事项

### 1. 调用架构

前端不直接调用 Python AI 服务，而是通过 Java 后端代理：

```
前端 ───JWT───▶ Java 后端 ───内部Token───▶ Python AI服务
```

**Java 后端职责**:
- 验证用户身份（JWT Token）
- 检查用户权限
- 记录调用日志
- 代理转发请求

**Python 服务职责**:
- 处理 AI 对话逻辑
- 调用 LLM API
- 返回响应

### 2. 前端调用 Java 后端

前端通过 Java 后端的 API 间接使用 AI 能力：

```javascript
// 前端调用 Java 后端
async function callAIAssistant(message, pageCode) {
  const token = localStorage.getItem('token');

  const response = await fetch('/api/ai/chat', {  // Java 后端地址
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      message: message,
      page_code: pageCode
    })
  });

  return response.json();
}

// 使用示例
const result = await callAIAssistant('请解释这个页面', 'homework_list');
console.log(result.data.response);
```

### 3. Java 后端转发到 Python

Java 后端收到请求后转发到 Python AI 服务：

```java
@Service
public class AIAssistantService {

    @Value("${ai.service.url}")
    private String aiServiceUrl;

    @Value("${ai.service.internal-token}")
    private String internalToken;

    public ChatResponse chat(Long userId, ChatRequest request) {
        // 构建转发请求
        Map<String, Object> body = new HashMap<>();
        body.put("message", request.getMessage());
        body.put("scene", "page_assistant");
        body.put("page_code", request.getPageCode());
        body.put("user_id", userId);  // 从 JWT 解析的用户ID

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("x-internal-token", internalToken);

        // 调用 Python 服务
        ResponseEntity<Map> response = restTemplate.postForEntity(
            aiServiceUrl + "/api/llm/chat",
            new HttpEntity<>(body, headers),
            Map.class
        );

        // 记录调用日志
        logService.log(userId, response.getBody().get("model_used"), ...);

        return convertResponse(response.getBody());
    }
}
```

### 4. 多轮对话

使用 `session_id` 保持会话上下文：

```javascript
// 前端代码
let sessionId = null;

async function chat(message) {
  const response = await fetch('/api/ai/chat', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({
      message: message,
      session_id: sessionId  // 第二次开始带上
    })
  });

  const result = await response.json();
  sessionId = result.data.session_id;  // 保存 session_id
  return result.data.response;
}

// 第一次对话
await chat('你好');
// 第二次对话（有上下文）
await chat('请继续');
```

### 5. 流式响应

Java 后端代理流式响应给前端：

```java
@GetMapping(value = "/api/ai/chat/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<String> streamChat(@AuthenticationPrincipal Long userId, ChatRequest request) {
    return webClient.post()
        .uri(aiServiceUrl + "/api/llm/chat/stream")
        .header("x-internal-token", internalToken)
        .bodyValue(Map.of(
            "message", request.getMessage(),
            "scene", "page_assistant",
            "user_id", userId
        ))
        .retrieve()
        .bodyToFlux(String.class);
}
```

---

*文档生成时间: 2025-03-20*