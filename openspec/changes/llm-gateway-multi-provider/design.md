## Context

### 当前状态
- AI 服务是一个**全新项目**，从零开始构建
- 现有代码库只有基础框架结构（main.py, api/, core/ 目录），核心逻辑为空
- 需要从头设计并实现 LLM Gateway 层

### 利益相关者
- **前端**：通过 Java 后端调用 AI 能力，不直接接触 Python 服务
- **Java 后端**：负责权限验证，代理转发请求到 Python AI 服务
- **运营**：需要成本监控和模型配置能力

### 架构关系
```
前端 ───JWT Token───▶ Java 后端 ───内部Token───▶ Python AI 服务
                        │                              │
                    权限验证                        LLM Gateway
                    用户管理                           │
                                                     ▼
                                              ┌─────────────────┐
                                              │ 智谱 / DeepSeek │
                                              │ / 百炼 API      │
                                              └─────────────────┘
```

### 约束
- Python 服务不直接暴露给前端，只接受 Java 后端内部调用
- Java 后端负责用户身份验证和权限控制
- API Key 不能暴露给前端（也不暴露给 Java 后端）
- 支持流式响应
- 支持 Function Calling（工具调用）

## Goals / Non-Goals

**Goals:**
- 建立统一的 LLM 调用层（使用 LangChain 抽象）
- 支持智谱、DeepSeek、百炼三家 LLM 厂商
- 支持按场景自动路由到最优模型（免费优先）
- 统一工具调用接口（LangChain bind_tools）
- API Key 通过环境变量安全管理

**Non-Goals:**
- 不实现协议转换层（Anthropic/OpenAI 协议适配）— 后续变更处理
- 不实现 MCP Client — 后续变更处理
- 不实现用户级模型配置 UI
- 不实现计费/额度管理系统
- 不自建 Provider 抽象（直接使用 LangChain）

## Decisions

### Decision 1: 使用 LangChain 作为 LLM 抽象层

**选择**: 使用 LangChain 的 ChatModel 抽象，不自建 Provider

```python
# LangChain 提供的 ChatModel 实现
from langchain_community.chat_models import ChatZhipuAI, ChatTongyi
from langchain_openai import ChatOpenAI
```

**理由**:
- LangChain 已有完善的 ChatModel 抽象
- 三家厂商都有官方/社区集成（ChatZhipuAI、ChatTongyi、ChatOpenAI 兼容 DeepSeek）
- 工具调用通过 `bind_tools()` 统一处理，无需自己适配格式
- 流式输出通过 `stream()` 统一接口
- 减少代码量和维护成本

**备选方案**:
- 自建 Provider 抽象: 更灵活，但工作量大，需要自己处理格式差异
- 直接使用厂商 SDK: 无抽象层，切换厂商成本高

### Decision 2: 模型工厂模式

**选择**: 使用工厂模式创建 LangChain ChatModel 实例

```python
class LLMFactory:
    @staticmethod
    def create(provider: str, model: str = None) -> BaseChatModel:
        if provider == "zhipu":
            return ChatZhipuAI(
                model=model or "glm-4-flash",
                zhipuai_api_key=settings.ZHIPU_API_KEY
            )
        elif provider == "deepseek":
            return ChatOpenAI(
                model=model or "deepseek-chat",
                openai_api_key=settings.DEEPSEEK_API_KEY,
                openai_api_base="https://api.deepseek.com/v1"
            )
        elif provider == "bailian":
            return ChatTongyi(
                model=model or "qwen-turbo",
                dashscope_api_key=settings.BAILIAN_API_KEY
            )
```

**理由**:
- 简单直观，易于扩展新厂商
- 配置集中管理
- 与模型路由器配合良好

### Decision 3: 模型路由策略

**选择**: 场景驱动路由 + 免费优先策略

```python
SCENE_MODEL_MAPPING = {
    "page_assistant": ("zhipu", "glm-4-flash"),      # 免费
    "homework_grading": ("deepseek", "deepseek-chat"), # 付费，需要深度理解
    "image_analysis": ("zhipu", "glm-4.6v"),         # 视觉模型
}
```

**理由**:
- 免费模型（GLM-4-Flash）覆盖 90% 场景
- 复杂任务自动路由到付费模型
- 配置驱动，易于调整

### Decision 4: API Key 安全存储

**选择**: 环境变量 + Pydantic Settings

```python
class Settings(BaseSettings):
    ZHIPU_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    BAILIAN_API_KEY: str = ""
    INTERNAL_TOKEN: str = ""  # Java 后端调用验证

    class Config:
        env_file = ".env"
```

**理由**:
- 不硬编码，不提交到 Git
- 支持 .env 文件本地开发
- 生产环境通过环境变量注入

**安全措施**:
- `.env` 加入 `.gitignore` ✓
- 创建 `.env.example` 模板（不含真实值）
- 生产环境使用密钥管理服务（如阿里云 KMS）
- Python 服务只接受 Java 后端内部调用（验证内部 Token）

### Decision 5: 工具调用使用 LangChain bind_tools

**选择**: 使用 LangChain 的 `bind_tools()` 统一工具调用

```python
from langchain_core.tools import tool

@tool
def search_questions(keyword: str, limit: int = 5) -> list:
    """搜索题库中的题目"""
    return []

# 创建模型并绑定工具
llm = LLMFactory.create("zhipu", "glm-4-flash")
llm_with_tools = llm.bind_tools([search_questions])

# 调用
response = llm_with_tools.invoke("帮我搜索数学题")

# 检查工具调用
if response.tool_calls:
    for tool_call in response.tool_calls:
        print(f"调用: {tool_call['name']}, 参数: {tool_call['args']}")
```

**理由**:
- LangChain 自动处理不同厂商的工具调用格式差异
- 统一的 `tool_calls` 返回格式
- 支持复杂的工具定义（嵌套参数等）

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 前端                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP (JWT Token)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Java 后端                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                    权限验证层                                        │  │
│   │   • JWT Token 验证                                                  │  │
│   │   • 用户权限检查                                                    │  │
│   │   • 调用限流                                                        │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    │ HTTP (内部 Token)                      │
│                                    ▼                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Python AI 服务                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                         API Layer                                    │  │
│   │   POST /api/chat  ←  Java 后端内部调用                               │  │
│   └────────────────────────────────┬────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                      Model Router (自己实现)                         │  │
│   │   scene → (provider, model) 映射                                     │  │
│   └────────────────────────────────┬────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                   LLM Factory (自己实现)                             │  │
│   │   创建 LangChain ChatModel 实例                                      │  │
│   └────────────────────────────────┬────────────────────────────────────┘  │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         ▼                          ▼                          ▼             │
│   ┌─────────────┐           ┌─────────────┐           ┌─────────────┐     │
│   │ChatZhipuAI  │           │ ChatOpenAI  │           │ ChatTongyi  │     │
│   │             │           │             │           │             │     │
│   │ Langchain   │           │ (DeepSeek)  │           │ Langchain   │     │
│   │ Community   │           │ Langchain   │           │ Community   │     │
│   └──────┬──────┘           └──────┬──────┘           └──────┬──────┘     │
│          │                         │                         │             │
└──────────┼─────────────────────────┼─────────────────────────┼─────────────┘
           │                         │                         │
           ▼                         ▼                         ▼
    ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
    │ 智谱 API    │           │ DeepSeek API│           │ 百炼 API    │
    └─────────────┘           └─────────────┘           └─────────────┘
```

**调用链路**:
```
前端 ──JWT──▶ Java后端 ──内部Token──▶ AI服务 ──▶ LLM Factory ──▶ LangChain ChatModel ──▶ LLM API
             (权限验证)               (路由)
```

**自己实现的部分**:
1. Model Router - 场景到模型的映射
2. LLM Factory - 创建 LangChain ChatModel 实例
3. 配置管理 - API Key、模型配置

**LangChain 提供的部分**:
1. ChatModel 抽象 - 统一调用接口
2. bind_tools() - 工具调用适配
3. stream() - 流式输出
4. 各厂商集成 - ChatZhipuAI, ChatTongyi, ChatOpenAI

## Risks / Trade-offs

### Risk 1: 免费模型限流
- **风险**: GLM-4-Flash 免费但可能有调用频率限制
- **缓解**: 实现降级机制，超出限流时切换到付费模型

### Risk 2: LangChain 版本兼容性
- **风险**: LangChain 更新可能破坏现有代码
- **缓解**:
  - 锁定版本 (requirements.txt)
  - 升级前测试

### Risk 3: API Key 泄露
- **风险**: .env 文件误提交到 GitHub
- **缓解**:
  - .gitignore 配置完整
  - .env.example 模板（不含真实值）
  - pre-commit hook 检查

### Risk 4: LangChain 依赖较大
- **风险**: LangChain 依赖包较多，增加部署体积
- **缓解**: 接受，换取开发效率

## Implementation Plan

### Phase 1: 基础设施（本周）
1. 配置 LangChain 依赖
2. 实现 LLM Factory
3. 实现智谱集成（GLM-4-Flash 免费）
4. 单元测试

### Phase 2: 扩展厂商（下周）
1. 实现 DeepSeek 集成（ChatOpenAI 兼容）
2. 实现百炼集成（ChatTongyi）
3. 实现模型路由器

### Phase 3: API 与集成（下周）
1. 实现对话 API 端点
2. 实现内部 Token 验证
3. 实现流式响应
4. 集成测试

## Open Questions

1. **内部 Token 生成方式？** → Java 后端生成，还是共享密钥？
2. **是否需要流式响应？** → 建议支持，LangChain stream() 已提供
3. **是否需要模型健康检查？** → 建议实现，用于监控各厂商 API 可用性
4. **调用日志存储位置？** → AI 服务返回 usage 信息，Java 后端记录完整日志