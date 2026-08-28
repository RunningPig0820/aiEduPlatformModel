## ADDED Requirements

### Requirement: 生成与强制引用

系统 SHALL 使用 doubao 流式生成回答，且**强制基于检索上下文**：prompt 约束"只基于检索上下文回答、每条引用标注来源页、无引用不输出正文"。

#### Scenario: 答案必须带引用

- **WHEN** 生成回答
- **THEN** 回答 SHALL 携带引用来源（页面+章节），无引用的输出 SHALL 被拒绝/修正

#### Scenario: 跨页按页引用

- **WHEN** 答案涉及多个页面（如"知识图谱如何支撑AI答疑"）
- **THEN** 回答 SHALL 按来源页分别标注（"知识图谱页§3 … AI答疑页§5 …"）

#### Scenario: 展示召回原文

- **WHEN** 生成回答后
- **THEN** 展示 SHALL 附带「召回文档原文」面板，显示本次检索命中的源文档段落

### Requirement: token usage 真算

系统 SHALL 在流式生成结束时读取真实 usage（prompt/completion tokens），并记录 embedding tokens 单独记账。

#### Scenario: 流式结束更新 usage

- **WHEN** doubao 流式生成结束
- **THEN** 系统 SHALL 从流结尾 usage chunk 读取并更新本轮 prompt/completion tokens

#### Scenario: usage 缺失降级估算

- **WHEN** 流式响应未返回 usage
- **THEN** 系统 SHALL 降级为 tokenizer 估算并标注"估算"，不阻塞回答展示

### Requirement: 成本展示

系统 SHALL 展示每轮成本：prompt/completion tokens、会话累计、¥ 换算（doubao 单价）；embedding tokens 单列。

#### Scenario: 每轮成本明细

- **WHEN** 一轮问答完成
- **THEN** 界面 SHALL 展示该轮 prompt/completion tokens、累计 tokens 与累计 ¥ 费用

### Requirement: 预置流程图

系统 SHALL 在命中"数据流"类问题时渲染完善文档第 4 节预置的 mermaid 数据流图；未预置时才动态生成兜底。

#### Scenario: 预置图渲染

- **WHEN** 问题命中数据流转类 chunk 且该 chunk 含预置 mermaid
- **THEN** 前端 SHALL 直接渲染 mermaid 图

#### Scenario: 无预置图兜底

- **WHEN** 命中 chunk 无预置 mermaid
- **THEN** 系统 SHALL 动态生成 mermaid 兜底，渲染失败则降级为文本描述
