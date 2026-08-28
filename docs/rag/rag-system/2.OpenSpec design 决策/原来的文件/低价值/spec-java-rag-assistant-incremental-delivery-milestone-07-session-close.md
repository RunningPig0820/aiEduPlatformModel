# milestone-07-session-close Specification

## Purpose

M7 交付"会话收尾"切片——显式关闭对话（close）、会话累计 token、trace_id 断线补查。本切片补上原清单缺失的会话闭环：学生可主动结束对话并结算会话累计 token，断线后可凭 trace_id 补查单轮结果。前端以关闭对话按钮 + 结算面板 + 断线重连补查验收，是全部链路的收尾切片。

## ADDED Requirements

### Requirement: 显式关闭对话与结算

M7 SHALL 交付 close 端点：`POST /api/rag/assistant/sessions/{sessionId}/close`（角色门同上，仅 STUDENT）——中止在途生成流（同 is_disconnected 取消）、session 状态置 closed（Redis）、返回会话累计 token（prompt/completion/cache_hit/total）+ 轮数。closed 会话再 ask → 固定话术"本轮对话已结束，可开启新对话"，0 token、不进 RAG 流程。close 幂等。

#### Scenario: 关闭返回累计 token

- **WHEN** 会话已有多轮，学生点击关闭对话
- **THEN** close 返回 closed=true、rounds=N、sessionUsage 四字段累计值，在途流中止

#### Scenario: 关闭后再问

- **WHEN** 会话已 closed，学生再次 ask 同 session
- **THEN** 固定话术"本轮对话已结束，可开启新对话"，tokensUsage=0

#### Scenario: 关闭幂等

- **WHEN** 已 closed 会话再次 close
- **THEN** 仍返回 closed=true + 当前累计值，不报错

### Requirement: 会话累计 token 聚合

M7 SHALL 交付会话累计：Java 每轮 done 后将 tokens_usage 累加进 Redis（`rag:assistant:session:{sessionId}:usage`，TTL 24h 对齐 tutoring），含轮数计数。close 时读回结算。

#### Scenario: 多轮累加

- **WHEN** 会话完成多轮（done 各带 usage）
- **THEN** Redis 会话累计 = 各轮之和（prompt/completion/cache_hit/total），close 返回该值

### Requirement: trace_id 断线补查

M7 SHALL 交付补查：每轮 done 后按 trace_id 落 Java Redis（`rag:assistant:trace:{traceId}`，TTL 24h）；`GET /api/rag/assistant/turns/{traceId}`（角色门同上）读 Redis 返回该轮完整结果（answer/quotedKeys/tokensUsage/suggestions）；trace 不存在 → 10002。供前端断线后凭 trace_id 单轮补查（不做会话恢复）。**turns 只存 Java Redis，Python 无状态不落会话 trace**（eval trace jsonl 与补查分开）。

#### Scenario: 断线补查成功

- **WHEN** 前端断线后凭 trace_id 补查
- **THEN** 返回该轮完整结果（answer/quotedKeys/tokensUsage/suggestions）

#### Scenario: 补查不存在

- **WHEN** trace_id 不存在
- **THEN** 返回 10002 trace 不存在

### Requirement: 里程碑对接测试验收

M7 SHALL 以会话收尾用例作为完成标准：RAG-CLOSE-001~006（关闭返回累计/关闭后再问/幂等/不存在会话/非学生/中止在途流）、RAG-COST-004~006（补查成功/不存在/非学生）。

#### Scenario: 对接测试全绿

- **WHEN** 前端完成关闭对话按钮 + 结算面板 + 断线补查对接
- **THEN** RAG-CLOSE-001~006、RAG-COST-004~006 通过，M7 视为完成

#### Scenario: 前端可见物

- **WHEN** 学生点击"结束对话"
- **THEN** 结算面板展示会话累计 token 与轮数；断线后前端可凭 trace_id 补查恢复单轮结果
