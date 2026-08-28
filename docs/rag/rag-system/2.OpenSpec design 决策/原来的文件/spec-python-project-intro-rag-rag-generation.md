> summary: 项目介绍RAG生成侧规范spec:doubao流式生成+强制基于检索上下文(无引用不输出正文、跨页按页标注、召回文档原文面板)、token usage真算(stream_options.include_usage流结尾usage chunk更新+embedding tokens单列+缺失降级tokenizer估算)、每轮成本展示(prompt/completion+累计+¥换算doubao单价)、预置mermaid流程图为主动态生成兜底。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-source/rag-system/OpenSpec设计决策/spec-python-project-intro-rag-rag-generation.md
> 类别: 操作流程

# spec-python-project-intro-rag-rag-generation(项目介绍 RAG 生成侧规范)

## 文档说明
> 本文件为原始 spec 文档的 RAG 结构化重构版本。
> ⚠️ 重要提示:本文属于**设计阶段素材**,为 08-21 源头设计,后续被 08-25 spec 部分反转;真实实现请以权威度 0.8 的 canonical 真相源文档与代码为准。本文件独立完整,内容不拆分到外部 canonical 文档。
> 设计演进备注:本 spec「打分 = 相似度 × 问题类型匹配 × 页面锚定加权」为 08-21 weighted-sum 口径,**08-25 已采用 RRF 融合替代 weighted-sum**(代码 `score = RRF × authority × anchor_w`);引用本 0.7 素材请核对代码确认实际落地状态。

### Requirement: 生成与强制引用
> 状态:⚠️
> 检索摘要:RAG 生成怎么强制引用?doubao流式只基于检索上下文回答、每条引用标注来源页、无引用不输出正文,为什么能堵死幻觉与跑题?

系统 SHALL 使用 doubao 流式生成回答,且**强制基于检索上下文**:prompt 约束"只基于检索上下文回答、每条引用标注来源页、无引用不输出正文"。

设计意图(为什么强制引用):**无引用不输出同时堵死幻觉和跑题**——"检索不到就边界拒绝,没引用就不输出正文";跨页答案按页分段引用,引用可回源。

#### Scenario: 答案必须带引用
- **WHEN** 生成回答
- **THEN** 回答 SHALL 携带引用来源(页面+章节),无引用的输出 SHALL 被拒绝/修正

#### Scenario: 跨页按页引用
- **WHEN** 答案涉及多个页面(如"知识图谱如何支撑AI答疑")
- **THEN** 回答 SHALL 按来源页分别标注("知识图谱页§3 … AI答疑页§5 …")

#### Scenario: 展示召回原文
- **WHEN** 生成回答后
- **THEN** 展示 SHALL 附带「召回文档原文」面板,显示本次检索命中的源文档段落

### Requirement: token usage 真算
> 状态:⚠️
> 检索摘要:流式token usage怎么真算?请求加stream_options.include_usage,流结束从结尾usage chunk更新本轮prompt/completion tokens,embedding tokens单独记账,缺失时tokenizer估算标注。

系统 SHALL 在流式生成结束时读取真实 usage(prompt/completion tokens),并记录 embedding tokens 单独记账。

设计意图(为什么真算):成本是 RAG 最大实战痛点;**真算 + 展示 = 成本控制叙事**;流式 usage 只在结尾返回 → "结束后更新"。

#### Scenario: 流式结束更新 usage
- **WHEN** doubao 流式生成结束
- **THEN** 系统 SHALL 从流结尾 usage chunk 读取并更新本轮 prompt/completion tokens

#### Scenario: usage 缺失降级估算
- **WHEN** 流式响应未返回 usage
- **THEN** 系统 SHALL 降级为 tokenizer 估算并标注"估算",不阻塞回答展示

### Requirement: 成本展示
> 状态:⚠️
> 检索摘要:每轮RAG成本怎么展示?prompt/completion tokens、会话累计、¥换算(doubao单价)三项,embedding tokens单列,成本如何可视可控?

系统 SHALL 展示每轮成本:prompt/completion tokens、会话累计、¥ 换算(doubao 单价);embedding tokens 单列。

#### Scenario: 每轮成本明细
- **WHEN** 一轮问答完成
- **THEN** 界面 SHALL 展示该轮 prompt/completion tokens、累计 tokens 与累计 ¥ 费用

### Requirement: 预置流程图
> 状态:⚠️
> 检索摘要:数据流类问题怎么渲染流程图?命中含预置mermaid的chunk时前端直接渲染,未预置才动态生成兜底,渲染失败降级为文本描述。

系统 SHALL 在命中"数据流"类问题时渲染完善文档第 4 节预置的 mermaid 数据流图;未预置时才动态生成兜底。

设计意图(为什么预置为主):**demo 可靠性优先**;预置图零渲染风险,动态生成仅兜底、演示不依赖。

#### Scenario: 预置图渲染
- **WHEN** 问题命中数据流转类 chunk 且该 chunk 含预置 mermaid
- **THEN** 前端 SHALL 直接渲染 mermaid 图

#### Scenario: 无预置图兜底
- **WHEN** 命中 chunk 无预置 mermaid
- **THEN** 系统 SHALL 动态生成 mermaid 兜底,渲染失败则降级为文本描述
