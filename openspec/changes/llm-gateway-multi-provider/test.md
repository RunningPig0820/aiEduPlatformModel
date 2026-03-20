# LLM Gateway 测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证 `LLM Gateway` 的所有业务场景，确保多 Provider 切换、模型路由、工具调用适配等功能的正确性和健壮性。

### 1.2 测试方式
- **单元测试**：测试 Provider 接口、路由器等独立组件
- **集成测试**：使用 pytest + httpx TestClient 调用真实 API
- **Mock 外部 API**：使用 `pytest-httpx` 或 `respx` mock LLM 厂商 API

### 1.3 测试环境配置
- pytest 配置：`pytest.ini`
- 环境：使用 `.env.test` 配置测试 API Key
- Mock：所有 LLM API 调用使用 mock，不实际调用厂商

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|-----|
| TEST_INTERNAL_TOKEN | test-internal-token | Java后端内部调用 Token |
| TEST_MESSAGE | 请解释这个页面 | 测试消息 |
| TEST_SCENE | page_assistant | 测试场景 |
| TEST_PAGE_CODE | homework_list | 测试页面编码 |
| TEST_SESSION_ID | sess_test_123 | 测试会话 ID |
| TEST_USER_ID | 12345 | 测试用户 ID |

---

## 3. 测试用例清单

### 3.1 Provider 注册表测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| REG-001 | 注册 Provider | 注册表为空 | Provider 实例 | Provider 存入注册表 |
| REG-002 | 获取已注册 Provider | Provider 已注册 | provider name | 返回 Provider 实例 |
| REG-003 | 获取未注册 Provider | Provider 未注册 | 不存在的 name | 抛出 ValueError |
| REG-004 | 列出所有 Provider | 多个 Provider 已注册 | 无 | 返回所有 Provider 名称列表 |

### 3.2 智谱 Provider 测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| ZHIPU-001 | 基础对话 | Mock API 返回正常响应 | messages, model=glm-4-flash | 返回 ChatResponse |
| ZHIPU-002 | 工具调用 | Mock API 返回 tool_calls | messages + tools | 返回包含 tool_calls 的响应 |
| ZHIPU-003 | 流式对话 | Mock SSE 流式响应 | messages, stream=True | 返回 AsyncIterator |
| ZHIPU-004 | API Key 从环境变量读取 | 设置 ZHIPU_API_KEY 环境变量 | 初始化 Provider | 使用环境变量中的 Key |
| ZHIPU-005 | API 调用失败 | Mock API 返回错误 | 无效请求 | 抛出 LLMError 异常 |
| ZHIPU-006 | 工具定义格式转换 | 无 | ToolDefinition 对象 | 转换为智谱/OpenAI 格式 |
| ZHIPU-007 | 工具调用结果解析 | 无 | 智谱 API 响应 | 解析为 ToolCall 对象 |

### 3.3 DeepSeek Provider 测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| DEEP-001 | 基础对话 | Mock API 返回正常响应 | messages, model=deepseek-chat | 返回 ChatResponse |
| DEEP-002 | 工具调用 | Mock API 返回 tool_calls | messages + tools | 返回包含 tool_calls 的响应 |
| DEEP-003 | OpenAI 协议兼容 | 无 | 请求格式 | 使用 OpenAI 兼容格式 |
| DEEP-004 | API Key 从环境变量读取 | 设置 DEEPSEEK_API_KEY 环境变量 | 初始化 Provider | 使用环境变量中的 Key |

### 3.4 阿里百炼 Provider 测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| BAIL-001 | 基础对话 | Mock dashscope SDK | messages, model=qwen-turbo | 返回 ChatResponse |
| BAIL-002 | 工具调用 | Mock SDK 返回 tool_calls | messages + tools | 返回包含 tool_calls 的响应 |
| BAIL-003 | API Key 从环境变量读取 | 设置 BAILIAN_API_KEY 环境变量 | 初始化 Provider | 使用环境变量中的 Key |

### 3.5 模型路由器测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| ROUTE-001 | 场景驱动路由 | 配置存在 | scene=page_assistant | 返回 (zhipu, glm-4-flash) |
| ROUTE-002 | 免费模型优先 | 免费模型配置存在 | scene=page_assistant | 返回免费模型 |
| ROUTE-003 | 未配置场景使用默认 | 场景未配置 | scene=unknown_scene | 返回默认模型 |
| ROUTE-004 | 复杂任务路由到付费模型 | 配置存在 | scene=homework_grading | 返回付费模型 |
| ROUTE-005 | 视觉任务路由到视觉模型 | 配置存在 | scene=image_analysis | 返回 glm-4.6v |

### 3.6 对话 API 测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| CHAT-001 | 基础对话成功 | Mock Provider, 有效内部Token | message + scene + user_id | 返回成功响应 |
| CHAT-002 | 指定 Provider 和模型 | Mock Provider, 有效内部Token | message + model_provider + model_name | 使用指定模型 |
| CHAT-003 | 自动路由模型 | Mock Provider, 有效内部Token | message + scene | 自动选择模型 |
| CHAT-004 | 内部 Token 验证失败 | 无效 token | 错误的 x-internal-token | 返回 403 |
| CHAT-005 | 参数校验-消息为空 | 无 | message="" | 返回参数错误 |
| CHAT-006 | 参数校验-缺少 user_id | 无 | 无 user_id | 返回参数错误 |
| CHAT-007 | 工具调用场景 | Mock 返回 tool_calls | message + tools | 返回 tool_calls |
| CHAT-008 | 多轮对话 | session 存在 | session_id | 包含历史上下文 |

### 3.7 流式对话 API 测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| STREAM-001 | 流式响应成功 | Mock Provider | message + scene | 返回 SSE 流 |
| STREAM-002 | 事件格式正确 | Mock Provider | message | 包含 token/done 事件 |
| STREAM-003 | 错误事件 | Mock 返回错误 | 触发错误的请求 | 返回 error 事件 |

### 3.8 获取模型列表 API 测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| MODEL-001 | 获取模型列表成功 | 无 | GET /api/llm/models | 返回所有 Provider 和模型 |
| MODEL-002 | 包含免费标记 | 无 | 无 | glm-4-flash 标记 free=true |
| MODEL-003 | 包含能力标记 | 无 | 无 | glm-4.6v 标记 supports_vision=true |

---

## 4. 错误码对照表

| 错误码 | 常量名 | 说明 |
|-------|-------|------|
| 00000 | SUCCESS | 成功 |
| 10001 | INVALID_PARAMS | 参数错误 |
| 10004 | UNAUTHORIZED | 未授权（内部 Token 无效） |
| 20001 | MODEL_UNAVAILABLE | 模型不可用 |
| 20002 | PROVIDER_NOT_REGISTERED | Provider 未注册 |
| 20003 | LLM_API_ERROR | API 调用失败 |
| 20004 | CONTENT_FILTERED | 内容审核不通过 |
| 20005 | RATE_LIMIT_EXCEEDED | 超出限流 |

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| Provider 注册表 | 4 |
| 智谱 Provider | 7 |
| DeepSeek Provider | 4 |
| 百炼 Provider | 3 |
| 模型路由器 | 5 |
| 对话 API | 8 |
| 流式对话 API | 3 |
| 模型列表 API | 3 |
| **总计** | **37** |

---

## 6. 测试执行顺序

测试按文件名和方法名顺序执行：

```
tests/
├── test_gateway_base.py      # Provider 接口测试
├── test_registry.py          # 注册表测试
├── test_zhipu_provider.py    # 智谱 Provider 测试
├── test_deepseek_provider.py # DeepSeek Provider 测试
├── test_bailian_provider.py  # 百炼 Provider 测试
├── test_router.py            # 路由器测试
├── test_chat_api.py          # 对话 API 测试
└── test_models_api.py        # 模型列表 API 测试
```

使用 `pytest-ordering` 或方法命名控制执行顺序。

---

## 7. 辅助方法

### 7.1 Mock 智谱 API 响应

```python
import respx
from httpx import Response

def mock_zhipu_chat_success():
    """Mock 智谱 API 成功响应"""
    return respx.post("https://open.bigmodel.cn/api/paas/v4/chat/completions").mock(
        return_value=Response(200, json={
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "这是一个测试响应"
                },
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        })
    )
```

### 7.2 创建测试请求头

```python
def create_internal_headers(token: str = "test-internal-token") -> dict:
    """创建 Java 后端内部调用认证头"""
    return {"x-internal-token": token}
```
```

### 7.3 创建测试请求

```python
def create_test_request() -> dict:
    """创建测试请求体"""
    return {
        "message": "请解释这个页面",
        "scene": "page_assistant",
        "page_code": "homework_list",
        "user_id": 12345
    }
```

### 7.4 Mock 工具调用响应

```python
def mock_tool_call_response():
    """Mock 工具调用响应"""
    return {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "search_questions",
                        "arguments": '{"keyword": "数学"}'
                    }
                }]
            },
            "finish_reason": "tool_calls"
        }]
    }
```

---

## 8. 运行测试

```bash
# 运行单个测试文件
pytest tests/test_zhipu_provider.py -v

# 运行单个测试方法
pytest tests/test_chat_api.py::test_chat_success -v

# 运行所有测试
pytest

# 运行并显示覆盖率
pytest --cov=ai_edu_ai_service --cov-report=term-missing

# 只运行单元测试（排除 API 测试）
pytest tests/test_*.py -v -k "not api"

# 运行集成测试
pytest tests/test_chat_api.py tests/test_models_api.py -v
```