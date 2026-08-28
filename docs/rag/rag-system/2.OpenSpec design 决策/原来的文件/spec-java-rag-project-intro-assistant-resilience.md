> summary: 本spec定义RAG项目介绍助手的韧性(resilience)能力：分层超时(召回2s/生成8s)、断连取消(is_disconnected)、超时降级话术写死0token、tokens_usage透明计费与会话累计、trace_id断线补查，保证对话不无限阻塞、不空转烧钱。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-source/rag-system/OpenSpec设计决策/spec-java-rag-project-intro-assistant-resilience.md
> 类别：开发难点

# rag-assistant-resilience Specification

## 文档说明
> 本文件为原始spec文档的RAG结构化重构版本。
> ⚠️重要提示：本文属于**设计阶段素材**，同时包含✅已落地、⚠️构想未实现、❓待决策内容；业务真实实现请以权威度0.8的canonical真相源文档为准。本文件独立完整，内容不拆分到外部canonical文档。

### 文档目的（Purpose）
> 状态：⚠️
> 检索摘要：会话过长或突然关闭时如何不无限阻塞、不空转烧钱？靠分层超时(召回2s/生成8s)、断连取消、降级话术0token、token累计与trace_id补查保障。

分层超时（召回 2s / 生成 8s）、断连取消（is_disconnected）、超时降级话术写死、tokens_usage 透明计费与 trace_id 断线补查。保证对话时间过长/对话突然关闭时不无限阻塞、不空转烧钱。

### 分层超时
> 状态：⚠️
> 检索摘要：召回层向量/BM25单路各2s、生成层8s硬超时；生成超时不报错，直接返回降级话术+已精排块清单供点击原文。

系统 SHALL 对链路各阶段设置硬超时：召回层（向量/BM25 单路）各 2s，生成层 8s。任何阶段超时不得无限阻塞。

#### Scenario: 召回单路超时降级
- **WHEN** 向量召回超过 2s 未返回
- **THEN** 系统降级该路为空并继续 BM25 路，链路继续，rerank 事件标记 degraded

#### Scenario: 生成超时返回召回清单
- **WHEN** 生成层超过 8s 未完成
- **THEN** 系统**不走 LLM**，直接返回固定降级话术："我找到了以下相关资料，但生成完整答案超时了，您可以直接点击查看原文：块1标题、块2标题、块3标题"，附带已精排块清单（点击查看原文）

### 超时降级话术写死
> 状态：⚠️
> 检索摘要：超时降级话术写死在代码中严禁调用LLM，保证降级路径0 token成本不烧钱。

系统 SHALL 将超时降级话术写死在代码中，**严禁调用 LLM 生成**，保证降级路径 0 token 成本。

#### Scenario: 降级零成本
- **WHEN** 生成超时降级
- **THEN** 返回写死话术 + 召回清单，不产生 LLM 调用

### 断连取消
> 状态：⚠️
> 检索摘要：SSE生成循环监听request.is_disconnected()，前端断开立即中止doubao流式请求，防止后端空转烧钱。

系统 SHALL 在 SSE 生成循环中监听前端连接状态（`request.is_disconnected()`）；一旦检测到前端主动断开，立即中止底层 LLM 流式请求，防止后端空转烧钱。

#### Scenario: 前端断开中止流
- **WHEN** 前端在生成中途关闭连接
- **THEN** 系统检测到 `is_disconnected()` 为真，中止上游 doubao 流，停止继续消耗 token

#### Scenario: 正常完成
- **WHEN** 前端保持连接至生成完成
- **THEN** 系统正常输出 token 流至 done，不触发取消

### tokens_usage 透明计费
> 状态：⚠️
> 检索摘要：done事件返回tokens_usage四字段，usage取流结束ark返回(include_usage)，取不到cache_hit_tokens用tokenizer估算标注。

系统 SHALL 在 `done` 事件返回 `tokens_usage` 对象，至少包含 `prompt_tokens`、`completion_tokens`、`cache_hit_tokens`、`total_tokens`；usage 取自流结束 ark 返回（`include_usage`），取不到 `cache_hit_tokens` 时用 tokenizer 估算并标注"估算"。

#### Scenario: 正常返回 usage
- **WHEN** 一轮生成完成
- **THEN** `done.tokensUsage` 返回四字段（prompt/completion/cache_hit/total），cache_hit 为真实值或标注估算

#### Scenario: 拒答/降级零 usage
- **WHEN** 范围门拒答或超时降级
- **THEN** `tokensUsage` 各字段为 0（未调 generate LLM）或仅含实际消耗（boundary 路径 recall 消耗不计入 usage 展示或单列）

### 会话累计 token（关闭对话结算）
> 状态：⚠️
> 检索摘要：每轮done后tokens_usage累加进Redis会话存储(rag:assistant:session:{id}:usage)，关闭对话返回累计token与轮数展示本次对话总消耗。

系统 SHALL 在每轮 `done` 后将 `tokens_usage` 累加至会话级存储（Redis，`rag:assistant:session:{sessionId}:usage`，TTL 对齐 tutoring 24h）；关闭对话时返回会话累计 `{prompt, completion, cache_hit, total}` 与轮数，供前端展示"本次对话总消耗"。

#### Scenario: 逐轮累加
- **WHEN** 会话内每轮正常完成
- **THEN** Java 将该轮 tokens_usage 累加进 Redis 会话累计，覆盖 prompt/completion/cache_hit/total 四字段

#### Scenario: 关闭时返回累计
- **WHEN** 学生调 close
- **THEN** 返回会话累计四字段 + 轮数，随后可清理会话状态

#### Scenario: 断连未关闭
- **WHEN** 前端断线（未显式 close）
- **THEN** 累计值保留在 Redis（TTL 内），不丢失；续接同 session_id 继续累加

### trace_id 生成与贯穿
> 状态：⚠️
> 检索摘要：每轮入口生成trace_id贯穿Java/Python两侧日志并在done返回，前端断线凭trace_id补查该轮完整结果。

系统 SHALL 在每轮入口生成 `trace_id`（Java 侧），透传 Python 贯穿两侧日志，并在 `done` 事件返回，供前端断线后凭 `trace_id` 补查该轮完整结果。

#### Scenario: trace_id 贯穿
- **WHEN** 一轮问答开始
- **THEN** Java 生成 trace_id，Python 侧同源贯穿，done 携带该 trace_id

#### Scenario: 断线补查
- **WHEN** 前端断线丢失结果，凭 trace_id 查询
- **THEN** 系统返回该轮完整结果（answer/quotedKeys/tokensUsage/suggestions）；超出保留窗口 → 明确"trace 不存在"

### 上下文窗口控制（history 截断）
> 状态：⚠️
> 检索摘要：组装intent/generate历史仅保留最近N轮(N=3可配置)防超context window，不设会话轮数上限持续可问。

系统 SHALL 在组装 intent/generate 的历史上下文时仅保留最近 N 轮问答（默认 N=3，可配置），防止历史无限膨胀导致超 context window、token 爆表与成本不可控。**不设会话轮数上限**——只要学生持续提问且每轮在窗口内，会话可持续。

#### Scenario: 超出窗口截断
- **WHEN** 会话历史超过最近 N 轮（如第 4 轮发起时，第 1 轮超出窗口）
- **THEN** 仅保留最近 N 轮问答进入 intent/generate 上下文，更早轮次截断（锚点由 session 独立携带，不受截断影响）

#### Scenario: 窗口内正常
- **WHEN** 会话历史 ≤ N 轮
- **THEN** 全部历史进入 intent/generate 上下文
