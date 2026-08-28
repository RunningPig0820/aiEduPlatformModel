# token成本与真算（会话结算）
> summary: token成本与真算（会话结算）
> 权威度: 0.8
> 模块: rag-system
> COS路径: rag-slices/rag-system/语雀/10-token成本与真算-2.md
> 类别：开发难点

---

> 检索摘要：会话累计 token 与断线结算闭环（场景26/27）：Java 网关以 sessionId 为键 Redis 累计会话 token+轮数、close 中止在途流+置 closed+返回累计值、closed 后再 ask 固定话术 0 token（每会话 token 预算上限是建议项未落地）；断线 trace_id 补查——白盒 Java 入口生成 traceId 随 permission 下发、每轮 done 快照 Redis TTL 24h、`GET /api/rag/assistant/turns/{traceId}` 补查（闭环），1.6C `/query` 路径无 trace_id 是死口。用户问"会话累计 token/close 结算/断线 trace 补查"时召回本块。

### 场景26：会话累计 token 与 close 结算
> 检索摘要【已落地·白盒】：Java 网关以 sessionId 为键 Redis 累计会话 token+轮数，close 时中止在途流+置 closed+返回累计值；closed 后再 ask 固定话术 0 token；每会话 token 预算上限是建议项。

| 属性 | 内容 |
|---|---|
| 业务场景 | 学生结束对话，需要整场累计 token 结算 |
| 触发条件 | 学生调 `POST /api/rag/assistant/sessions/{sessionId}/close`；或断连未 close 续接 |
| 当前处理 | Java Redis `rag:assistant:session:{sessionId}:usage` 累计（D-C）；close 中止在途流+置 closed+返回 `{sessionUsage, rounds}`；closed 后再 ask → 固定话术"本轮对话已结束，可开启新对话" 0 token 不进 RAG 流程；close 不存在/已 closed 幂等（10002） |
| 兜底降级策略 | 断连未 close 时累计保留 Redis 续接；Python 无状态不落会话 |
| 残余风险 | 会话 token 预算上限（如 50k 到顶提示开新会话）是建议项#13 未落地；前端刷新后 sessionId 丢失（前端生成 UUID 整场复用，刷新即新会话） |

> 证据：详见 `1.语雀/语雀-边界场景清单.md`（§场景26）｜ spec-java-rag-project-intro-assistant-gateway；spec-frontend-rag-assistant-frontend-rag-assistant-ui；[总揽§3.4/§4.4]

### 场景27：断线后 trace_id 补查（1.6C 死口 vs 白盒闭环）
> 检索摘要【已落地·白盒 / 1.6C 死口】：白盒路径已闭环——permission 事件带 traceId 流开始即可取，Java Redis 每轮 done 快照 TTL 24h，`GET /api/rag/assistant/turns/{traceId}` 补查；1.6C 路径无 trace_id 补查是死口。

| 属性 | 内容 |
|---|---|
| 业务场景 | 前端断线丢失某轮结果，凭 trace_id 补查 |
| 触发条件 | SSE 流中断（permission 已到、done 未到）；或 done 后想回看历史 |
| 当前处理 | 白盒：Java 入口生成 trace_id 随 permission 下发（D-B），每轮 done 快照存 Redis（`rag:assistant:trace:{traceId}` TTL 24h），`GET /api/rag/assistant/turns/{traceId}` 读回（超窗→10002）；前端用 permission.traceId 流开始即存，任意阶段断连可补查 |
| 兜底降级策略 | done.traceId 与 permission.traceId 一致性校验（不一致告警不阻断）；前端提示重发问题 |
| 残余风险 | 1.6C `/query` 路径无 trace_id（无补查能力）；整场会话持久化/断线恢复（多轮续接）明确不做（08-25 定稿仅单轮补查）；Redis TTL 24h 超窗补查返回 10002 |

> 证据：详见 `1.语雀/语雀-边界场景清单.md`（§场景27）｜ spec-java-rag-project-intro-assistant-gateway；spec-frontend-rag-assistant-frontend-rag-assistant-ui；[总揽§4.4/§9.2#11/#12]
