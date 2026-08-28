# milestone-04-generate-token Specification

## Purpose

M4 交付"生成 + token 展示"切片——doubao 流式生成（8s 超时降级话术、断连取消）、tokens_usage 四字段 + trace_id、done 事件重建。本切片替换 M2/M3 的 generate 桩替，接真实生成，前端流式展示回答与成本面板。**token 展示（原清单 #1）在本切片落地——token 需生成完才有，这是依赖序修正的核心。**

## ADDED Requirements

### Requirement: doubao 流式生成与超时降级

M4 SHALL 交付生成阶段：doubao 流式生成回答（`token*` 事件逐块透传）；8s 硬超时 → 不走 LLM，返回召回清单 + 固定话术"我找到了以下相关资料，但生成完整答案超时了，您可以直接点击查看原文：块1、块2、块3"（0 额外 token）；`is_disconnected()` 检测到前端断开 → 中止上游 doubao 流。

#### Scenario: 流式回答展示

- **WHEN** 学生提问命中语料且生成正常
- **THEN** 前端逐 token 流式渲染回答，整轮以 done 收尾

#### Scenario: 生成超时降级

- **WHEN** 生成超过 8s
- **THEN** 返回召回清单 + 固定超时话术，不调 LLM 重试，0 额外 token

#### Scenario: 断连取消

- **WHEN** 流式生成中前端断开连接
- **THEN** Java/Python 检测到断开，中止上游 doubao 流，不空转烧钱

### Requirement: tokens_usage 透明计费

M4 SHALL 交付 token 展示：done 事件携带 `tokens_usage{prompt_tokens, completion_tokens, cache_hit_tokens, total_tokens}`（cache_hit 取不到 → tokenizer 估算标注"估算"）+ `trace_id`。前端成本面板实时/最终展示四字段。

#### Scenario: 成本面板展示

- **WHEN** 一轮生成完成
- **THEN** done 携带完整 tokens_usage（四字段），前端成本面板展示 prompt/completion/cache_hit/total

#### Scenario: cache_hit 估算

- **WHEN** doubao 未返回 cache_hit_tokens
- **THEN** 以 tokenizer 估算值填充并标注"估算"，不报错

### Requirement: done 事件重建

M4 SHALL 交付 done 事件：Java 重建（不透传 Python 原始 meta/done），字段含 answer/tokensUsage/traceId；quotedKeys/suggestions 在 M5/M6 补充（契约冻结：字段追加不重排）。

#### Scenario: done 完整字段

- **WHEN** 一轮生成完成
- **THEN** done 含 answer + tokensUsage（四字段）+ traceId，前端可结束本轮渲染

### Requirement: 里程碑对接测试验收

M4 SHALL 以真实生成链路 + 计费用例作为完成标准：RAG-SSE-001（全量时序 permission→intent→rewrite→rerank→token*→done）、RAG-COST-001（四字段）、RAG-COST-007（会话累计累加，M7 结算复用）、RAG-ABORT-001（断连取消）。生成桩替在本切片移除。

#### Scenario: 对接测试全绿

- **WHEN** Python 完成真实 generate，前端完成流式回答 + 成本面板对接
- **THEN** RAG-SSE-001（全量）、RAG-COST-001/007、RAG-ABORT-001 通过，M4 视为完成

#### Scenario: 前端可见物

- **WHEN** 学生提问命中语料
- **THEN** 前端流式渲染回答 + 成本面板展示本轮四字段 token 消耗
