# 分析-08-Java后端网关与SSE中继-落地问题与复盘-2
> summary: Java网关SSE中继方案对账复盘
> 来源: 切片 ｜ 锚点: 落地问题与复盘-2
> 节: 分析-08-Java后端网关与SSE中继
> COS路径: rag-slices/interview/rag-system/分析-08-Java后端网关与SSE中继-落地问题与复盘-2.md
> 类别：开发难点
> target: 面试项目问答

---

## 对账复盘（原始方案 → 实际落地 → 差异影响）

### 方案 vs 实现

**1. 角色门在 Java、禁信 body**：原始方案「从可信 session 取角色，非 STUDENT 固定 403，body 传 role 忽略」；实际落地完全一致，命令无 role 字段、角色只认 session、测试覆盖多角色场景。✅ 落地，无差异。

**2. permission 携带 trace_id**：原始方案 permission 由 Java 前置、带 trace，Python 无感；实际落地一致，permission 是流首事件、traceId 由 Java 生成、桥还防御性过滤 Python 侧 permission。✅ 落地。

**3. sessionId 前端生成、close 未知报错**：原始方案 sessionId 前端 UUID 复用、ask 未知按新会话、close 未知报业务码 10002；实际落地一致。✅ 落地。

**4. 查看原文走 Java 代理**：原始方案前端不直连 Python、GET source 经 Java 转发；实际落地一致（绝对 URI + 逐段 URL 编码）。✅ 落地。

**5. source 前缀白名单 / COS 读归属**：任务清单把「source 代理(COS 读/前缀白名单)」写在 Java；实际**翻转**——Java 侧无白名单、无 COS 读，白名单与 COS 读都在 Python 侧（只放行 rag-source/ 与 rag-slices/ 前缀），Java 是纯 HTTP 转发。⚠️ **差异影响**：安全前置在 Python 单点，Java 无二次拦截，若 Python 白名单被绕过则 Java 兜不住。

**6. close 中止在途流**：原始方案 close 语义含「中止该会话在途生成流」；实际**翻转**——close 只置标志 + 读回累计，无在途流中止逻辑，中止由 Python 断连检测负责。⚠️ **差异影响**：close 后用户仍可能收到在途 token/done。

**7. 非流式 done + stages**：原始方案 /ask/sync 返回 done + stages 摘要；实际**翻转**——是 M1 桩替，硬编码占位话术不调 Python，真实 Python 非流式未接，流式 ask 恒 stream=true。⚠️ **差异影响**：非流式端点拿到的是占位答案，不是真实回答。

**8. turns 只存 Java Redis**：原始方案每轮 done 按 trace_id 落 Redis TTL 24h、补查读 Redis；实际落地一致。✅ 落地。

**9. history 前端传不落库**：原始方案 history 最近 3 轮由 Java 透传 Python、刷新后空=新会话；实际落地一致，Java 不落库。✅ 落地。

**10. 会话累计 token 归 Java**：原始方案 Java 每轮 done 累加、close 读回；实际落地一致。✅ 落地。

**11. 真实对话质量打分**：原始方案评估报告含 realConversation 区段（Java 每轮 LLM 打分累计）；实际落地为 Java 侧新增能力，4 维度 0-5 打分异步旁路。✅ 落地。

### 契约 vs 实现

**12. SSE 事件时序与字段**：原始方案 permission→intent→(clarify|switch)→rewrite→rerank→(boundary)→token*→done 全 camelCase；实际落地一致，桥保序中继 + 逐事件重建，测试验证全序与字段。✅ 落地。

**13. reject 事件**：早期「禁区硬拒答」设计有 reject 事件；实际**已废弃**——DTO 保留定义但不产出，唯一拒答路径是 boundary low_confidence。✅ 已废弃（留 DTO 完整性）。

**14. degraded 标记透传**：Python 注释声明「供 done/boundary 透传 degraded 语义」；实际**翻转**——Python rerank/done 事件不带 degraded，Java rerank DTO 也无 degraded 字段。⚠️ **差异影响**：前端拿不到降级信号，无法显式提示用户「这轮是降级回答」。

**15. CLOSED_MSG 对齐**：原始方案 close 后 ask 返回「本轮对话已结束，可开启新对话」；实际落地一致，Java 常量与 Python 端常量完全相同，close 后短路 0 token。✅ 落地。

> 证据：详见 `3.代码/分析-08-Java后端网关与SSE中继.md`（§对账要点）｜ `4.完善文档/08-*.md`
