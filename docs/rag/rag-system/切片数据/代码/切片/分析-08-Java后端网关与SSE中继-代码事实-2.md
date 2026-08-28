# 分析-08-Java后端网关与SSE中继-代码事实-2
> summary: Java网关会话结算与代理代码事实
> 来源: 切片 ｜ 锚点: 代码事实-2
> 节: 分析-08-Java后端网关与SSE中继
> COS路径: rag-slices/rag-system/代码/分析-08-Java后端网关与SSE中继-代码事实-2.md
> 类别：架构设计
> target: 开发对账

---

## 代码事实

### 4. Redis 会话累计 / close 结算 / turns 补查

Redis 键与 TTL（AppService:72-81）：

| 键 | 用途 | TTL |
|---|---|---|
| `rag:assistant:session:{sessionId}:usage` | 会话累计 token+轮数（每轮 done 累加，close 读回） | 24h |
| `rag:assistant:session:{sessionId}:closed` | 会话关闭标志（值 "1"） | 24h |
| `rag:assistant:trace:{traceId}` | 每轮 done camel JSON 快照（断线补查） | 24h |
| `rag:assistant:eval:recent` | 真实对话质量聚合（每轮 LLM 打分累计） | 24h |

- **每轮 done 落库** `persistRound`（AppService:392-405）：done 的 **camel JSON** 直接写 trace 键（`redisService.set(TRACE_KEY_PREFIX+traceId, ev.data(), 24h)`）；再 `accumulateSessionUsage` 把 tokens_usage 读-改-写累加进 session usage 键（prompt/completion/cacheHit/total 各 nvl 0，rounds+1；AppService:408-423）。落库失败只告警，不阻断回答链路。
- **close 结算**（AppService:138-167）：读 usage 键 + closed 键；两者皆 null → `EntityNotFoundException("会话不存在")`（业务码 10002，GlobalExceptionHandler 转 HTTP 404）；closed 为 null → 写 `closed="1"`（TTL 24h）；读回累计 → `RagCloseDTO{sessionId, closed:true, rounds, sessionUsage{prompt/completion/cacheHit/total}}`。**幂等**：已 closed 不重复写标志，仍返回 closed=true。
- **close 后再 ask 短路** `isSessionClosed`（AppService:364-374）+ `closedSessionStream`（AppService:377-386）：`closed="1"` → 返回 permission + done(固定话术 `CLOSED_MSG="本轮对话已结束，可开启新对话。"`，tokensUsage 全 0，suggestions 空)，不调 Python、不落库、不评分。Redis 异常 → 按未关闭处理不阻断（AppService:369-373）。CLOSED_MSG 与 Python `assistant.py:165` 写死常量一致。
- **turns 断线补查**（AppService:172-180）：读 `rag:assistant:trace:{traceId}`，null → `EntityNotFoundException("trace 不存在")`（10002）；否则 `CAMEL_MAPPER.readValue(json, SseDoneDTO.class)` 返回完整结果（answer/quotedKeys/tokensUsage/suggestions）。

### 5. source 代理（查看原文）

- Controller → AppService.source → Bridge.source（AppService:186-188 纯委托）。
- Bridge（Bridge:130-151）：把 filePath 按 `/` 分段逐段 `URLEncoder.encode`（保留目录结构，中文/空格安全）后拼 `/`；**必须用绝对 URI**（`.uri(URI)`，相对路径无 scheme/host 无法与 baseUrl 拼接 → WebClientRequestException）；`GET {baseUrl}/api/rag/source/{encodedPath}`；onStatus 404 → `EntityNotFoundException("原文不存在")`；传输异常 → `TutoringAgentException("RAG 原文服务暂不可用")`。
- **COS 读与前缀白名单在 Python 侧**，不在 Java：Python `api/rag.py:50-72` 的 `/api/rag/source/{file_path:path}` 从 COS 普通桶 `ai-edu-1318177119` 读文件，且 `file_path.startswith(("rag-source/","rag-slices/"))` 才放行（防任意 COS key 读取），读失败 → 404「文件不存在」。Java 的 `CosFileStorageServiceImpl` 是通用文件存储（tutoring transcript 归档等），**不参与 RAG source 代理链路**。

### 6. eval/guide 代理

- **evalReport**（AppService:194-204）：桥返回 Python 原始 snake JSON → `SNAKE_MAPPER.readValue(json, RagEvalReportDTO.class)`，再 `setRealConversation(readRealConversation())` 并入 Java 侧真实对话质量。Python 暂无报告 → 404「暂无评估报告」→ Java `EntityNotFoundException`。`RagEvalReportDTO` 用 `@JsonAlias("hit_at_3")`/`@JsonAlias("precision_at_3")` 收 Python 字段（SNAKE_CASE 策略只把 hitAt3 翻成 hit_at3，数字前不加下划线，ReportDTO:33-35, 49-52）。
- **realConversation 读取**（AppService:207-231）：读 `rag:assistant:eval:recent`，`count==0`/无 key/解析失败 → null（前端不展示该区段）；avgQuality=sum_quality/count、quotedRatio=quoted_count/count、avgLatencyMs=sum_latency_ms/count。
- **evalRun**（AppService:237-245）：桥 POST Python `/eval/run`（异步后台线程跑评测，立即返回），`already_running=true` 幂等非错误；SNAKE_MAPPER 解析 `{running, already_running}` → `{running, alreadyRunning}`。
- **guide**（AppService:252-260）：桥 GET Python `/guide?current_project=`（缺省不发参，Python FALLBACK_MODULE=ai-tutoring 兜底），SNAKE_MAPPER 解析 `{suggestions:[{title,direction}]}` → RagGuideDTO。0 token、非 SSE、不占冻结时序。

### 9. 非流式 /ask/sync 是桩替

- `askStages`（AppService:432-443）：**不调 Python**，硬编码返回 `answer="（桩替）RAG 项目介绍助手链路已通，等待 Python 白盒引擎接入。"` + `stages=["permission","intent","rewrite","rerank","done"]`；用 `LinkedHashMap` 允许 `reason:null`（`Map.of` 不允许 null 值会 NPE）。真实 Python 非流式（`req.stream=false`）Java 侧**未接**——ask() 恒传 `stream=TRUE`（AppService:112），RagAskCommand.stream 字段在 /ask 路径实际被忽略。

> 证据：详见 `3.代码/分析-08-Java后端网关与SSE中继.md`（§代码事实 4/5/6/9）
