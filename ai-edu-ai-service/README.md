# LLM Gateway 使用示例

## 环境配置

```bash
# 1. 复制环境变量模板
cp ai-edu-ai-service/.env.example ai-edu-ai-service/.env

# 2. 编辑 .env 填入真实 API Key
vim ai-edu-ai-service/.env
```

## 启动服务

```bash
cd ai-edu-ai-service
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API 调用示例

### 1. 基础对话

```bash
curl -X POST http://localhost:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -H "x-internal-token: your-internal-token" \
  -d '{
    "message": "请解释这个页面的功能",
    "scene": "page_assistant",
    "user_id": 12345
  }'
```

响应:
```json
{
  "response": "这个页面是...",
  "session_id": "uuid-xxx",
  "model_used": "zhipu/glm-4-flash",
  "usage": {"total_tokens": 100}
}
```

### 2. 指定模型

```bash
curl -X POST http://localhost:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -H "x-internal-token: your-internal-token" \
  -d '{
    "message": "批改这道数学题",
    "scene": "homework_grading",
    "user_id": 12345,
    "model_provider": "deepseek",
    "model_name": "deepseek-chat"
  }'
```

### 3. 流式响应

```bash
curl -X POST http://localhost:8000/api/llm/chat/stream \
  -H "Content-Type: application/json" \
  -H "x-internal-token: your-internal-token" \
  -d '{
    "message": "请解释这个页面",
    "scene": "page_assistant",
    "user_id": 12345
  }'
```

SSE 响应格式:
```
event: token
data: {"content": "这"}

event: token
data: {"content": "是"}

event: done
data: {"model_used": "zhipu/glm-4-flash", "usage": {...}}
```

### 4. 获取可用模型列表

```bash
curl -X GET http://localhost:8000/api/llm/models \
  -H "x-internal-token: your-internal-token"
```

### 5. 多轮对话

```bash
# 第一次对话
curl -X POST http://localhost:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -H "x-internal-token: your-internal-token" \
  -d '{
    "message": "你好",
    "scene": "page_assistant",
    "user_id": 12345
  }'
# 返回 session_id: "sess-xxx"

# 后续对话带上 session_id
curl -X POST http://localhost:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -H "x-internal-token: your-internal-token" \
  -d '{
    "message": "请继续",
    "scene": "page_assistant",
    "user_id": 12345,
    "session_id": "sess-xxx"
  }'
```

## Java 后端集成示例

```java
@Service
public class AIAssistantService {

    @Value("${ai.service.url}")
    private String aiServiceUrl;

    @Value("${ai.service.internal-token}")
    private String internalToken;

    public ChatResponse chat(Long userId, String message, String scene) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("x-internal-token", internalToken);

        Map<String, Object> body = new HashMap<>();
        body.put("message", message);
        body.put("scene", scene);
        body.put("user_id", userId);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);

        ResponseEntity<Map> response = restTemplate.postForEntity(
            aiServiceUrl + "/api/llm/chat",
            request,
            Map.class
        );

        return convertResponse(response.getBody());
    }
}
```

## 场景说明

| Scene | 描述 | 默认模型 | 免费 |
|-------|------|---------|------|
| page_assistant | 页面 AI 助手 | glm-4-flash | ✓ |
| faq | 常见问题 | glm-4-flash | ✓ |
| homework_grading | 作业批改 | deepseek-chat | - |
| image_analysis | 图片分析 | glm-4.6v | - |
| content_generation | 内容生成 | deepseek-chat | - |

## 工具调用示例 (bind_tools)

```python
from langchain_core.tools import tool
from core.gateway.factory import LLMFactory

@tool
def search_questions(keyword: str, limit: int = 5) -> list:
    """搜索题库"""
    return []

llm = LLMFactory.create("zhipu", "glm-4-flash")
llm_with_tools = llm.bind_tools([search_questions])

response = llm_with_tools.invoke("帮我搜索数学题")

if response.tool_calls:
    for tc in response.tool_calls:
        print(f"工具: {tc['name']}, 参数: {tc['args']}")
```