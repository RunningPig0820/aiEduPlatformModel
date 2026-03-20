## ADDED Requirements

### Requirement: LLM Factory

系统 SHALL 提供 `LLMFactory` 工厂类，创建 LangChain ChatModel 实例。

#### Scenario: 创建智谱 ChatModel
- **WHEN** 调用 `LLMFactory.create("zhipu", "glm-4-flash")`
- **THEN** 系统 SHALL 返回配置好的 ChatZhipuAI 实例

#### Scenario: 创建 DeepSeek ChatModel
- **WHEN** 调用 `LLMFactory.create("deepseek", "deepseek-chat")`
- **THEN** 系统 SHALL 返回配置好的 ChatOpenAI 实例（指向 DeepSeek API）

#### Scenario: 创建百炼 ChatModel
- **WHEN** 调用 `LLMFactory.create("bailian", "qwen-turbo")`
- **THEN** 系统 SHALL 返回配置好的 ChatTongyi 实例

#### Scenario: 未知 Provider 抛出异常
- **WHEN** 调用 `LLMFactory.create("unknown", ...)`
- **THEN** 系统 SHALL 抛出 `ValueError` 异常

---

### Requirement: 智谱 AI 集成

系统 SHALL 通过 LangChain ChatZhipuAI 集成智谱 AI，支持 GLM 系列模型。

#### Scenario: 支持的模型列表
- **WHEN** 使用智谱集成
- **THEN** 系统 SHALL 支持 `glm-4-flash` 模型（免费）
- **AND** 系统 SHALL 支持 `glm-4.5-air` 模型
- **AND** 系统 SHALL 支持 `glm-4.6v` 模型（视觉）
- **AND** 系统 SHALL 支持 `glm-4.7` 模型

#### Scenario: 基础对话
- **WHEN** 调用 ChatZhipuAI 的 invoke 方法
- **THEN** 系统 SHALL 返回 AIMessage 响应

#### Scenario: 工具调用支持
- **WHEN** 使用 bind_tools 绑定工具后调用
- **THEN** 系统 SHALL 支持工具调用
- **AND** 响应中 SHALL 包含 tool_calls 字段

#### Scenario: API Key 安全存储
- **WHEN** 初始化智谱集成
- **THEN** API Key SHALL 从环境变量 `ZHIPU_API_KEY` 读取

---

### Requirement: DeepSeek 集成

系统 SHALL 通过 LangChain ChatOpenAI 兼容模式集成 DeepSeek。

#### Scenario: 支持的模型列表
- **WHEN** 使用 DeepSeek 集成
- **THEN** 系统 SHALL 支持 `deepseek-chat` 模型
- **AND** 系统 SHALL 支持 `deepseek-coder` 模型

#### Scenario: OpenAI 协议兼容
- **WHEN** 创建 DeepSeek ChatModel
- **THEN** 系统 SHALL 配置 `openai_api_base="https://api.deepseek.com/v1"`

#### Scenario: 工具调用支持
- **WHEN** 使用 bind_tools 绑定工具后调用
- **THEN** 系统 SHALL 支持工具调用

#### Scenario: API Key 安全存储
- **WHEN** 初始化 DeepSeek 集成
- **THEN** API Key SHALL 从环境变量 `DEEPSEEK_API_KEY` 读取

---

### Requirement: 阿里百炼集成

系统 SHALL 通过 LangChain ChatTongyi 集成阿里百炼。

#### Scenario: 支持的模型列表
- **WHEN** 使用百炼集成
- **THEN** 系统 SHALL 支持 `qwen-turbo` 模型
- **AND** 系统 SHALL 支持 `qwen-plus` 模型

#### Scenario: 工具调用支持
- **WHEN** 使用 bind_tools 绑定工具后调用
- **THEN** 系统 SHALL 支持工具调用

#### Scenario: API Key 安全存储
- **WHEN** 初始化百炼集成
- **THEN** API Key SHALL 从环境变量 `BAILIAN_API_KEY` 读取

---

### Requirement: 模型路由器

系统 SHALL 提供模型路由器，根据场景自动选择最优模型。

#### Scenario: 场景驱动路由
- **WHEN** 调用 `ModelRouter.get_model("page_assistant")`
- **THEN** 系统 SHALL 返回适合页面助手场景的 (provider, model) 元组

#### Scenario: 免费模型优先
- **WHEN** 场景配置了免费模型（如 glm-4-flash）
- **THEN** 系统 SHALL 优先返回免费模型

#### Scenario: 默认模型
- **WHEN** 请求的场景未配置
- **THEN** 系统 SHALL 返回默认模型 `("zhipu", "glm-4-flash")`

---

### Requirement: 工具调用支持

系统 SHALL 使用 LangChain 的 bind_tools 统一工具调用接口。

#### Scenario: 定义工具
- **WHEN** 使用 `@tool` 装饰器定义函数
- **THEN** 系统 SHALL 自动生成工具定义

#### Scenario: 绑定工具到模型
- **WHEN** 调用 `llm.bind_tools([tool1, tool2])`
- **THEN** 系统 SHALL 返回绑定了工具的模型

#### Scenario: 获取工具调用结果
- **WHEN** 模型决定调用工具
- **THEN** 响应中 SHALL 包含 `tool_calls` 列表
- **AND** 每个 tool_call SHALL 包含 `name` 和 `args`

---

### Requirement: 流式输出支持

系统 SHALL 使用 LangChain 的 stream 方法支持流式输出。

#### Scenario: 流式调用
- **WHEN** 调用 `llm.stream(messages)`
- **THEN** 系统 SHALL 返回 AsyncIterator

#### Scenario: 获取流式内容
- **WHEN** 迭代 stream 返回值
- **THEN** 每个迭代项 SHALL 包含 AIMessageChunk

---

### Requirement: 配置管理

系统 SHALL 提供安全的配置管理，支持环境变量和 .env 文件。

#### Scenario: 环境变量读取
- **WHEN** 系统加载配置
- **THEN** API Key SHALL 从环境变量读取
- **AND** 支持 .env 文件作为本地开发配置源

#### Scenario: 敏感信息保护
- **WHEN** 项目提交到 Git
- **THEN** .env 文件 SHALL NOT 被提交
- **AND** .env.example SHALL 被提交（不含真实值）

---

### Requirement: 内部 Token 验证

系统 SHALL 验证 Java 后端的内部调用 Token。

#### Scenario: 有效 Token
- **WHEN** 请求携带正确的 `x-internal-token` 头
- **THEN** 系统 SHALL 允许调用

#### Scenario: 无效 Token
- **WHEN** 请求携带错误或缺失的 `x-internal-token` 头
- **THEN** 系统 SHALL 返回 403 Forbidden