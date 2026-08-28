# token成本与真算
> summary: token成本与真算
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-rag-project-intro-assistant-resilience-10-token成本与真算.md
> 类别：数据存储

---

## 文档说明
> 本文件由 OpenSpec 设计素材（spec-python-rag-project-intro-assistant-resilience.md）按业务主题「token成本与真算」重切合并。
> ⚠️设计阶段素材：真实实现以权威度 0.8 的 canonical 真相源 + 代码为准（代码已部分落地）；含 ✅已落地 / ⚠️构想未实现 / ❓待决策 内容，引用需核对代码。

### Requirement: tokens_usage 透明计费
> 检索摘要：token 计费怎么透明——done 返回四字段 usage、cache_hit 取不到就估算标注？

系统 SHALL 在 done 返回 tokens_usage `{prompt_tokens, completion_tokens, cache_hit_tokens, total_tokens}`；usage 取流结束 ark 返回（include_usage）；cache_hit 取不到 → tokenizer 估算标注"估算"。

#### Scenario: 正常返回 usage
- **WHEN** 一轮生成完成
- **THEN** done.tokensUsage 四字段齐全，cache_hit 为真实值或标注估算

#### Scenario: 拒答/降级零 usage
- **WHEN** 范围门拒答或超时降级
- **THEN** tokensUsage 各字段 0（未调 generate LLM）

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-resilience.md`（§Requirement: tokens_usage 透明计费）

### Requirement: 会话累计 token（由 Java 网关聚合）
> 检索摘要：会话累计 token 谁聚合——Python 无状态、Java 网关 Redis 累加、close 时读回？

系统 SHALL 保持 Python **无状态**——每轮仅产出 per-turn tokens_usage；会话累计 token 由 Java 网关每轮累加（Redis），`POST /sessions/{sessionId}/close` 时读回返回累计值 + 轮数。Python 不建会话状态（除非 Java 不聚合，需明确）。

#### Scenario: 关闭结算
- **WHEN** 学生 `POST /sessions/{sessionId}/close`
- **THEN** Java 读回会话累计 token + 轮数返回（Python 无状态，仅支持 is_disconnected 中止在途流）

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-resilience.md`（§Requirement: 会话累计 token）
