# rag-assistant-resilience Specification

## Purpose

分层超时（召回 2s / 生成 8s）、断连取消（is_disconnected）、超时降级话术写死（0 token）、tokens_usage 透明计费 + trace_id 断线补查。保证对话超时/断开时不无限阻塞、不空转烧钱。

## ADDED Requirements

### Requirement: 分层超时

系统 SHALL 对链路各阶段设硬超时：召回层（向量/BM25 单路）各 2s，生成层 8s。任何阶段超时不得无限阻塞。

#### Scenario: 召回单路超时降级
- **WHEN** 向量召回超 2s 未返回
- **THEN** 该路降级为空继续 BM25，链路继续，rerank 标记 degraded

#### Scenario: 生成超时返回召回清单
- **WHEN** 生成层超 8s 未完成
- **THEN** 不走 LLM，直接固定降级话术："我找到了以下相关资料，但生成完整答案超时了，您可以直接点击查看原文：块1、块2、块3"，附精排块清单

### Requirement: 超时降级话术写死

系统 SHALL 将超时降级话术写死在代码，严禁调 LLM 生成，降级路径 0 token。

#### Scenario: 降级零成本
- **WHEN** 生成超时降级
- **THEN** 写死话术 + 召回清单，无 LLM 调用

### Requirement: 断连取消

系统 SHALL 在 SSE 生成循环监听 `request.is_disconnected()`；检测到前端断开 → 立即中止底层 doubao 流式请求，防后端空转烧钱。

#### Scenario: 前端断开中止流
- **WHEN** 前端在生成中途关闭连接
- **THEN** 检测 is_disconnected → 中止上游 doubao 流，停止消耗 token

#### Scenario: 正常完成
- **WHEN** 前端保持连接至生成完成
- **THEN** 正常输出 token 流至 done，不触发取消

### Requirement: tokens_usage 透明计费

系统 SHALL 在 done 返回 tokens_usage `{prompt_tokens, completion_tokens, cache_hit_tokens, total_tokens}`；usage 取流结束 ark 返回（include_usage）；cache_hit 取不到 → tokenizer 估算标注"估算"。

#### Scenario: 正常返回 usage
- **WHEN** 一轮生成完成
- **THEN** done.tokensUsage 四字段齐全，cache_hit 为真实值或标注估算

#### Scenario: 拒答/降级零 usage
- **WHEN** 范围门拒答或超时降级
- **THEN** tokensUsage 各字段 0（未调 generate LLM）

### Requirement: trace_id 断线补查

系统 SHALL 每轮生成 `trace_id`（Java 生成透传或 Python 生成，贯穿日志）；`GET /api/rag/assistant/turns/{traceId}` 返回该轮 done 结果（answer/quotedKeys/tokensUsage/suggestions/reason），供前端断线后补查。

#### Scenario: 断线补查
- **WHEN** 前端断线后凭 trace_id 补查
- **THEN** 返回该轮完整结果（若 trace 超保留窗口 → 10002）

### Requirement: 会话累计 token（由 Java 网关聚合）

系统 SHALL 保持 Python **无状态**——每轮仅产出 per-turn tokens_usage；会话累计 token 由 Java 网关每轮累加（Redis），`POST /sessions/{sessionId}/close` 时读回返回累计值 + 轮数。Python 不建会话状态（除非 Java 不聚合，需明确）。

#### Scenario: 关闭结算
- **WHEN** 学生 `POST /sessions/{sessionId}/close`
- **THEN** Java 读回会话累计 token + 轮数返回（Python 无状态，仅支持 is_disconnected 中止在途流）
