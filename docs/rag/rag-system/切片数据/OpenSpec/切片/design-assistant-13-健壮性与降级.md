# 健壮性与降级（分层超时 2s/8s / 断连取消 / 会话截断）

> summary: 健壮性与降级 — 双路超时（向量 2s / 生成 8s）+ is_disconnected 断连取消 + history 会话截断 + trace 补查归 Java
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-assistant-13-健壮性与降级.md
> 类别：开发难点


### D-B. 双路超时（pipeline/resilience）

> 检索摘要：双路召回和生成怎么设超时——向量 2s、生成 8s，超时降级话术写死？

- 向量路/COS 可能阻塞：用 `asyncio.wait_for(retrieve_vector(...), timeout=2)`（若 retrieve 是同步，包 `run_in_threadpool` + 超时）；BM25 本地快，超时留给网络路。
- 生成 8s：`ark_stream.stream_chat` 已是 httpx 流式，超时由 httpx `timeout` 控制 + 外层捕获 → 写死降级话术。

### D-D. 会话状态（close/trace_id）——定死 2026-08-25

> 检索摘要：会话状态与断连补查谁管——Python 无状态、close=Java 关中继、is_disconnected 中止 doubao、turns 补查存 Java Redis？

- **Python 保持无状态**：history/trace_id 由 Java 网关传入（请求字段），Python 只消费。
- **trace_id**：定死 Java 生成 → 请求传 Python → Python 贯穿日志并在 done 回显；Python 不自己生成。
- **close**：Python **不建 close 端点**——close = Java 关中继 → Python `is_disconnected()` 中止 doubao + Java Redis 置 closed + 返回累计。
- **turns 补查**：存 Java Redis（聚合点），Python 不落会话 trace。Python 的 eval trace jsonl 是评估用，与会话补查分开。

### D-A2. 会话截断（history 显式截断）

> 检索摘要：会话截断怎么做——取 history[-N:] 最近 N 轮，后端 resilience spec 的上下文窗口，Java 组装 Python 只消费+截断？

- **显式截断**：取 `history[-N:]`（最近 N 轮），后端 resilience spec 的上下文窗口。history 由 Java 网关组装传入，Python 只消费+截断。

### 白盒链路（超时 / 断连段）

> 检索摘要：白盒链路中超时与断连的降级路径——向量 2s 超时降级、生成 8s 超时固定话术+召回清单、is_disconnected 中止流？

```
 → recall(向量2s超时降级 + BM25) → 按 anchor 选池
 → generate(doubao 流式, 8s 超时→固定话术+召回清单)
     ←── is_disconnected → 中止流
```

### Risks / Trade-offs（健壮性相关）

> 检索摘要：双路超时实现复杂度与 history 时序对不上的风险——run_in_threadpool+wait_for 包裹测降级、定死契约联调核对？

- [双路超时实现复杂度] asyncio vs 同步检索 → 用 run_in_threadpool + wait_for 包裹，测超时降级路径。
- [history 由 Java 传、时序对不上] 定死契约：Java 组装 history/trace_id，Python 只消费+截断；联调时逐轮核对。
