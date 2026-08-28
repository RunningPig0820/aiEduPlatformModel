# 分析-08-Java后端网关与SSE中继-架构与技术取舍
> summary: Java网关SSE中继架构与技术取舍
> 来源: 切片 ｜ 锚点: 架构与技术取舍
> 节: 分析-08-Java后端网关与SSE中继
> COS路径: rag-slices/interview/rag-system/分析-08-Java后端网关与SSE中继-架构与技术取舍.md
> 类别：架构设计
> target: 面试项目问答

---

## 架构与技术取舍

### 1. 端点与角色硬门

对外 8 类端点，全部先过角色硬门：流式提问 ask、非流式 ask/sync（桩替）、查看原文 source、评估报告 eval/report、评估重跑 eval/run、开始引导 guide、关闭会话结算 close、断线补查 turns。

**角色硬门**是网关第一道闸：只从可信 HttpSession 取 role，`role=="STUDENT"` 才放行；非 STUDENT / 无 session 固定返回 403「仅学生可访问此助手」，**不进 RAG、不调 LLM、不产生 trace**。**body 传 role 一律忽略**——前端命令没有 role 字段，角色只认 session，测试明确验证「TEACHER session + body 带 role=STUDENT → 仍 403」。设计取舍：Controller 侧角色门**只查 role、不校验 userId 登录态**，与同步业务的鉴权口径不同，缺 userId 但 role=STUDENT 的会话理论可通过（对账里是隐性坑）。

### 2. SSE 事件中继机制

- **三层中继**：桥做原始中继（过滤 Python 侧 permission）→ 应用层逐事件重建（snake→camel）→ 前端按 camelCase 契约消费。
- **traceId 由 Java 入口生成**（UUID）；**permission 事件仅 Java 前置发**（role/allowed/traceId），是流的第一个事件，流一开始前端即可拿 traceId（断线补查不依赖 done）。
- **事件重建**：intent/rewrite/rerank/boundary/clarify/switch/token/done 统一走「snake 读 → DTO → camel 写」；**未知事件/解析失败透传原始**，不阻断链路（代价是前端若按 camel 解析拿不到字段）。
- **done 的 traceId 一致性校验**：Python 回显与 Java 生成不一致 → 仅告警不阻断（契约定稿）。
- **前端事件契约**（全 camelCase）：permission、intent（含 anchor/category/switchDetected/ambiguous/candidates/lockedSections/degraded）、rewrite（originalQuestion/rewrittenQuery）、rerank（blocks 数组）、boundary（唯一拒答路径，reason=low_confidence）、clarify（candidates/default）、switch（fromAnchor/toAnchor）、token（text）、done（answer/quotedKeys/tokensUsage{prompt/completion/cacheHit/total}/traceId/suggestions/reason）。**reject 事件是遗留 DTO，已被 boundary 取代，当前不产出**。

### 3. Redis 会话聚合（Java 是会话状态点）

Python 保持无状态，所有会话状态归 Java Redis，TTL 24h：

- **会话累计**：每轮 done 落库，tokens_usage 读-改-写累加进会话 usage 键（prompt/completion/cacheHit/total + rounds）。
- **trace 快照**：每轮 done 的 camel JSON 写 trace 键，供断线补查。
- **close 结算**：读 usage + closed 键，两者皆空 → 业务码 10002「会话不存在」（HTTP 404）；否则置 closed 标志并读回累计 token/轮数返回给前端；**幂等**——已 closed 不重复写。
- **close 后再 ask 短路**：返回固定话术「本轮对话已结束，可开启新对话。」（与 Python 端常量一致），0 token、不调 Python、不落库、不评分；Redis 异常按未关闭处理不阻断。
- **turns 断线补查**：按 traceId 读 done camel 快照返回完整结果（answer/quotedKeys/tokensUsage/suggestions）。

### 4. 蛇↔驼双契约纪律

前端 camel / 内部 snake 双契约各自稳定：Java→Python 命令经注解序列化为 snake_case（session_id/current_project/trace_id/top_k），前端命令用 camelCase；SSE 端点直接返回 `Flux<ServerSentEvent<String>>`，不包 ResponseEntity（包了会丢泛型、Spring MVC 找不到 converter）。评价报告数字字段用别名收 Python 下划线字段（hit_at_3→hitAt3、precision_at_3→precisionAt3）；clarify 的 `default` 字段用注解避开 Java 关键字。宽容 ObjectMapper（忽略未知字段）保证契约字段追加不破坏。

### 5. 非流式 /ask/sync 是桩替

askStages **不调 Python**，硬编码返回占位话术「RAG 项目介绍助手链路已通，等待 Python 白盒引擎接入。」+ stages 摘要列表；用允许 null 值的 LinkedHashMap（Map.of 不允许 null 会 NPE）。真实 Python 非流式能力存在但 Java 未接——ask() 恒传 stream=true，前端命令的 stream 字段在 /ask 路径实际被忽略。

> 证据：详见 `3.代码/分析-08-Java后端网关与SSE中继.md`（§代码事实 1/2/3/4/9）｜ `4.完善文档/08-*.md`
