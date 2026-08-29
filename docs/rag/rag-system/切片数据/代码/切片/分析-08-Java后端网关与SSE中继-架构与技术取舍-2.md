# 分析-08-Java后端网关与SSE中继-架构与技术取舍-2
> summary: Java网关代理与质量打分架构技术取舍
> 来源: 切片 ｜ 锚点: 架构与技术取舍-2
> 节: 分析-08-Java后端网关与SSE中继
> COS路径: rag-slices/rag-system/代码/分析-08-Java后端网关与SSE中继-架构与技术取舍-2.md
> 类别：架构设计
> target: 面试项目问答

---

## 架构与技术取舍（续）

### 6. source / eval / guide 代理

- **查看原文 source**：Java 纯委托转发 Python，filePath 按 `/` 逐段 URL 编码（保留目录结构、中文/空格安全）、必须用绝对 URI（相对路径无 scheme/host 无法与 baseUrl 拼接）；Python 404 → Java 明确提示「原文不存在」。**关键取舍：COS 读与前缀白名单在 Python 侧，不在 Java**——Python 只放行 rag-source/ 与 rag-slices/ 前缀、从 COS 普通桶读文件（防任意 COS key 读取）；Java 侧无白名单、无 COS 读，是纯 HTTP 转发；Java 的通用 COS 文件存储不参与 RAG source 链路。
- **评估报告 eval/report**：桥取 Python 原始 snake JSON → 反序列化 → 并入 Java 侧真实对话质量区段（realConversation）。Python 暂无报告 → 明确 404「暂无评估报告」。
- **评估重跑 eval/run**：桥 POST Python 异步后台线程跑评测、立即返回，`already_running=true` 幂等非错误。
- **开始引导 guide**：桥 GET Python 模块引导底座池（缺省模块有兜底），0 token、非 SSE、不占冻结时序。

### 7. 真实对话质量打分（评估报告 realConversation）

**机制**：每个 done 事件异步触发打分——复用 LLM 网关按 4 维度（相关性/完整性/忠实度/清晰度）打 0-5 整数分，忠实度优先级最高（编造 → 总分最高 2 分），「无引用片段」特殊规则=忠实度不扣分；要求 LLM 输出 JSON {"score","reason"}。**尽力而为旁路**：跳过条件=answer 空/blank、boundary/timeout 轮、问候语轮（固定欢迎语 0 token）、无打分器注入；打分失败静默不入累计、不打断问答链路；打分在弹性调度线程池异步执行。

**实现细节**：打分场景专用标识 + 系统用户 0L 哨兵（Python 端 user_id 必填）+ 20s 超时；打分 prompt 要求引用片段摘要（优先取 quotedKeys 命中的精排块，最多 5 条，800 字上限按整块截断不硬切）；宽容解析 LLM 输出（容忍 JSON 外套代码块，score 越界走兜底）；累计写评估聚合键（count/sum_quality/quoted_count/sum_latency_ms，TTL 24h）。评估报告 realConversation 区段由聚合数据算 avgQuality/quotedRatio/avgLatencyMs，count 为 0 或解析失败则前端不展示该区段。

### 8. 桥与 WebClient 配置

Java→Python 桥基于 WebClient：baseUrl 取配置 + 默认带内部鉴权头（复用 llm-gateway 内部鉴权模式）；连接超时 5s、响应超时 60s。ask 流式用 POST + TEXT_EVENT_STREAM；Java→Python 命令序列化为 snake_case；**流式不可重试**（重试会重发已透传事件），失败由编排层降级、抛「RAG 助手服务暂不可用」；Python 鉴权失败（token 缺失/不符）映射为网关异常。内部契约含 question/session_id/current_project/history(前端最近 3 轮含 clarify)/trace_id/top_k/stream(恒 true)。

### 9. 设计要点（取舍总结）

- **角色门收敛在 Java**：前端只走 Java 网关，Python 不自己认证、不碰会话、保持无状态；permission 由 Java 前置，Python 生产端点从 intent 开始。非 STUDENT → 固定 403、不进 RAG、不调 LLM、不产生 trace。
- **SSE 中继三层**：桥原始中继（滤 permission）→ 应用层重建（snake→camel）→ 前端消费；宽容反序列化保证契约字段追加不破坏（契约冻结：字段追加不重排）。
- **Java 是会话聚合点**：每轮 done 过手即累计（usage + trace 快照 + 质量分），Python 无状态；close 结算、turns 断线补查、closed 短路话术全归 Java Redis，TTL 24h 对齐 tutoring。
- **质量打分是尽力而为旁路**：异步、失败不入累计、无打分器不打断链路——评估 realConversation 与离线 benchmark 并存展示。
- **蛇↔驼双契约纪律**：序列化注解 + 双 ObjectMapper + 数字字段别名 + Java 关键字规避，四件套保证前端 camel / 内部 snake 各自稳定。
- **容错与降级**：done traceId 不一致仅告警；重建失败透传原始；Redis 读写失败只告警；桥流式失败冒泡由编排层降级；close/turn 未知 → 业务码 10002 明确提示，不静默返回空。

> 证据：详见 `3.代码/分析-08-Java后端网关与SSE中继.md`（§代码事实 5/6/7/8 / §设计要点）｜ `4.完善文档/08-*.md`
