# 分析-08-Java后端网关与SSE中继-落地问题与复盘
> summary: Java网关SSE中继落地问题与复盘
> 来源: 切片 ｜ 锚点: 落地问题与复盘
> 节: 分析-08-Java后端网关与SSE中继
> COS路径: rag-slices/interview/rag-system/分析-08-Java后端网关与SSE中继-落地问题与复盘.md
> 类别：开发难点
> target: 面试项目问答

---

## 隐性坑与注意事项

1. **非流式 /ask/sync 是桩替，不是真实非流式链路**：返回硬编码占位话术，不调 Python；真实 Python 非流式能力存在但 Java 未接，流式 ask 恒走 stream=true。
2. **close 不中止在途生成流**：设计文档写「close 中止在途流」，代码只有「置 closed 标志 + 读回累计」；close 与断连取消（Python 侧 is_disconnected 检测）是两条独立路径，Java 侧 close 不会掐掉 Python 上游流。
3. **角色门只查 role、不查 userId**：网关侧角色判定只比对会话 role 是否为 STUDENT，与同步业务先校验 userId 登录态的鉴权口径不同；缺 userId 但 role=STUDENT 的会话理论可放行（鉴权盲点）。
4. **SSE 事件重建失败/未知事件透传原始**：未知事件（如 Python 流内 error）与解析失败都按原样透传 snake_case，前端若按 camel 契约解析会拿不到字段——是「不阻断链路」的代价。
5. **Python 降级标记（degraded）不达前端**：Python 召回阶段返回 degraded 列表，但 rerank/done 事件不带；Java 的 rerank DTO 也只有 blocks 字段无 degraded 字段——前端看不到「这轮是降级回答」的显式信号。
6. **trace 快照存的是 camel JSON**：断线补查读回的是已重建的 camel 快照；若 Python 契约升级新增字段，宽容反序列化（忽略未知字段）会静默丢弃新字段，补查结果可能不全。
7. **Redis 读-改-写非原子**：会话累计、质量分累计、close 结算都是 get→改→set，多轮并发/多实例部署下可能覆盖丢计数（无 Lua 脚本或分布式锁）。
8. **桥 ask 失败不重试**：流式不可重试（重试会重发已透传事件），Python 挂 → 异常直接冒泡，前端整轮失败（无降级 done），与其它查询端点的降级语义不同。
9. **source 代理 Java 侧无前缀白名单**：防任意路径读取的检查只在 Python 侧，Java 桥只做 URL 编码转发；若 Python 端白名单被绕过，Java 无二次拦截（安全单点前置）。
10. **done.answer 与 token 流的关系**：done.answer 是全量答案，token 事件是增量；前端若以 done 为准，token 只作「流式渲染」用；质量打分也以 done.answer 为准。

> 证据：详见 `3.代码/分析-08-Java后端网关与SSE中继.md`（§隐性坑与注意事项）｜ `4.完善文档/08-*.md`
