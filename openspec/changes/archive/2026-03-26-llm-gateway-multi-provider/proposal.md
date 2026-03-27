## Why

AI 服务是全新项目，需要建立 LLM 调用层，存在以下需求：
1. **厂商灵活切换**：支持智谱、DeepSeek、百炼等多家 LLM 提供商，避免厂商锁定
2. **成本控制**：免费模型（如 GLM-4-Flash）可覆盖 90% 场景，大幅降低成本
3. **API Key 安全**：Key 不能暴露给前端，需要安全管控
4. **开发效率**：使用 LangChain 成熟框架，减少自建代码量

## What Changes

- 新增 **LLM Gateway 层**：使用 LangChain ChatModel 抽象，统一 LLM 调用接口
- 新增 **LLM Factory**：工厂模式创建 LangChain ChatModel 实例
- 新增 **模型路由策略**：按场景自动选择最优模型（免费模型优先）
- 新增 **工具调用支持**：使用 LangChain bind_tools 统一工具调用
- 新增 **安全管控**：API Key 环境变量管理，.gitignore 保护

## Capabilities

### New Capabilities

- `llm-gateway`: LLM 网关核心，使用 LangChain ChatModel 抽象，包含 LLM Factory、统一响应格式
- `llm-zhipu`: 智谱 AI 集成（LangChain ChatZhipuAI），支持 GLM-4-Flash（免费）、GLM-4.5-Air、GLM-4.6V、GLM-4.7
- `llm-deepseek`: DeepSeek 集成（LangChain ChatOpenAI 兼容），支持 deepseek-chat、deepseek-coder
- `llm-bailian`: 阿里百炼集成（LangChain ChatTongyi），支持 qwen-turbo、qwen-plus
- `model-router`: 模型路由器，按场景自动选择最优模型（免费优先策略）
- `tool-calling`: 工具调用支持，使用 LangChain bind_tools 统一接口

### Modified Capabilities

无（这是新增功能，不修改现有能力的需求定义）

## Impact

**新增文件**：
- `core/gateway/factory.py` - LLM 工厂，创建 LangChain ChatModel 实例
- `core/gateway/router.py` - 模型路由器
- `models/chat.py` - 统一数据模型
- `config/settings.py` - 配置管理（API Key 从环境变量读取）
- `config/model_config.py` - 模型配置
- `api/chat.py` - 对话 API 端点
- `.env.example` - 环境变量模板

**依赖变更**：
- 新增 `langchain` 核心库
- 新增 `langchain-community`（ChatZhipuAI, ChatTongyi）
- 新增 `langchain-openai`（ChatOpenAI 兼容 DeepSeek）
- 新增 `langchain-core`（工具定义等）

**安全要求**：
- API Key 仅存储在环境变量，不硬编码
- .env 文件加入 .gitignore，不提交到 GitHub
- 不向前端暴露任何 Key 信息
- Python 服务只接受 Java 后端内部调用