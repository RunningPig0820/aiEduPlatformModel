## 1. 基础设施搭建

- [x] 1.1 更新 `requirements.txt` 添加 LangChain 依赖
  - langchain
  - langchain-community
  - langchain-openai
  - langchain-core
- [x] 1.2 创建 `config/settings.py` 配置管理（Pydantic Settings）
- [x] 1.3 创建 `.env.example` 模板文件
- [x] 1.4 确认 `.gitignore` 忽略 `.env` 文件

## 2. LLM Factory 实现

- [x] 2.1 创建 `core/gateway/` 目录结构
- [x] 2.2 创建 `core/gateway/factory.py` LLM 工厂
- [x] 2.3 实现 `create(provider, model)` 方法
- [x] 2.4 创建统一的数据模型 `models/chat.py`

## 3. 智谱集成（LangChain ChatZhipuAI）

- [x] 3.1 验证 langchain-community 的 ChatZhipuAI 集成
- [x] 3.2 配置智谱 API Key（环境变量）
- [x] 3.3 测试 glm-4-flash 模型调用
- [x] 3.4 测试工具调用（bind_tools）
- [x] 3.5 测试流式输出（stream）

## 4. DeepSeek 集成（LangChain ChatOpenAI 兼容）

- [x] 4.1 配置 ChatOpenAI 使用 DeepSeek API Base
- [x] 4.2 配置 DeepSeek API Key
- [x] 4.3 测试 deepseek-chat 模型调用
- [x] 4.4 测试工具调用
- [x] 4.5 测试流式输出

## 5. 阿里百炼集成（LangChain ChatTongyi）

- [x] 5.1 验证 langchain-community 的 ChatTongyi 集成
- [x] 5.2 配置百炼 API Key（dashscope）
- [x] 5.3 测试 qwen-turbo 模型调用
- [x] 5.4 测试工具调用
- [x] 5.5 测试流式输出

## 6. 模型路由器

- [x] 6.1 创建 `config/model_config.py` 模型配置
- [x] 6.2 创建 `core/gateway/router.py` 模型路由器
- [x] 6.3 实现 `get_model(scene)` 场景驱动路由
- [x] 6.4 实现免费模型优先逻辑
- [x] 6.5 实现默认模型 fallback

## 7. API 端点实现

- [x] 7.1 创建 `api/chat.py` 对话 API 端点
- [x] 7.2 实现内部 Token 验证中间件
- [x] 7.3 实现请求参数验证（Pydantic）
- [x] 7.4 实现场景参数传递和模型路由
- [x] 7.5 实现流式响应 (SSE)
- [x] 7.6 返回使用的模型信息给 Java 后端

## 8. 工具调用支持

- [x] 8.1 创建工具定义模板
- [x] 8.2 实现 bind_tools 集成
- [x] 8.3 实现工具调用结果处理
- [x] 8.4 测试多工具场景

## 9. 测试

- [x] 9.1 创建 `tests/test_factory.py` 测试 LLM Factory
- [x] 9.2 创建 `tests/test_zhipu.py` 测试智谱集成（mock API）
- [x] 9.3 创建 `tests/test_deepseek.py` 测试 DeepSeek 集成
- [x] 9.4 创建 `tests/test_bailian.py` 测试百炼集成
- [x] 9.5 创建 `tests/test_router.py` 测试模型路由器
- [x] 9.6 创建 `tests/test_chat_api.py` 测试对话 API

## 10. 文档与收尾

- [x] 10.1 更新 CLAUDE.md 添加 Gateway 架构说明
- [x] 10.2 创建 API 使用示例
- [x] 10.3 配置文件验证（确保生产环境配置正确）