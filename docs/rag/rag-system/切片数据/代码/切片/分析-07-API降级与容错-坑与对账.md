# 分析-07-API降级与容错-坑与对账

> summary: API降级与容错隐性坑与对账复盘坑与对账
> 来源: 切片 ｜ 锚点: 坑与对账
> 节: 分析-07-API降级与容错
> COS路径: rag-slices/rag-system/代码/分析-07-API降级与容错-坑与对账.md
> 类别：开发难点
> target: 开发对账

---

## 隐性坑

- **范围门 0.75/0.5 只在白盒链路生效，1.6C /query 没有置信度门**：api/rag.py:120 只有 `if not hits`（空命中拒答），模块 docstring（api/rag.py:13）却写「置信度过低 → 拒答」——面试时若说「所有端点都有 0.75/0.5 范围门」会被 1.6C 端点反证。真实是：白盒 A9 有阈值门（assistant.py:388-408），1.6C 端点只有空命中门。
- **`DEGRADED_VECTOR`/`DEGRADED_BM25` 标记定义了但未透传**：`recall` 返回 `degraded` 列表（assistant.py:112-116, 129），注释声明「供 done/boundary 事件透传 degraded 语义」（26-28 行），但 `pipeline_events` 的 rerank 事件只发 `{"blocks":...}`（613）、done 事件只走 `assemble_done`（无 degraded 参数，505-518）——降级标记实际没进任何 SSE 事件，前端拿不到「这轮是降级」的显式信号。
- **1.6C 端点生成失败降级不区分超时/异常**：doubao 挂只有一种话术「生成服务不可用」（api/rag.py:133），而白盒链路区分 `GEN_TIMEOUT_MSG`/`GEN_FAIL_MSG` 且 reason 统一 "timeout"（assistant.py:161-162, 483）。
- **`_llm_intent`/`_llm_category` 关重试（max_retries=0）+ 20s 超时**：意图判断失败就降级关键词，不会重试拖慢；但代价是网络抖动时意图质量不稳（对账 K1 的「6/10→10/10」就是靠 LLM 而非关键词）。
- **查看原文的 404 语义**：读 COS 失败与「文件不存在」都返回 404（api/rag.py:66, 71），前端无法区分「真的没有」vs「COS 挂了」——但换来了不暴露内部错误。
- **评测边界拒答走 `_boundary_trace` 而非普通链路**：边界拒答类型 0 token、quoted 空、score 0/5 二值（eval_agent.py:307-347），聚合时 `judged=True` 但 `hit=False`/`precision=0`——评测报告里边界用例与普通用例指标不可混读。
- **流式生成断连只在 generate 前/中检测**：`request.is_disconnected()` 在 generate 前（assistant.py:628-630）和每轮 queue.get 前（460-462）检测，但注释明确「不掐 httpx 流，在途流由前端取消」——断开后到下一次检测之间有残留 token 会继续产出。

## 对账要点（原始方案 → 实际落地 → 业务影响）

1. **范围门 0.75/0.5**：语雀/完善文档 09 口径称「范围门(后置)：检索置信度阈值——索引层 0.75 / 源文档池 0.5」是全局机制；实际只在白盒链路 A9 生效（assistant.py:388-408 + pipeline_events:616-625）并作用于评测边界类型（eval_agent.py:307-347），而 1.6C /query 端点没有此门、只有 `if not hits` 空命中拒答。**翻转结论：范围门仅部分落地——白盒有、1.6C 端点无**，1.6C 低置信但非空的命中会照常进 generate，前端在 1.6C 端拿不到置信度拦截。
2. **1.6C「置信度过低 → 拒答」注释**：api/rag.py:13 模块 docstring 自称降级语义含「置信度过低 → 拒答」；实际代码只判 `not hits`（api/rag.py:120-126），不读置信度。**翻转结论：docstring 高于实际**——按注释理解会高估 1.6C 端点的拦截能力。
3. **token usage 真算**：语雀-问题4 指出「现有代码在丢 usage」，建议加 `stream_options.include_usage` + 抓结尾 usage chunk；现状为流式白盒已修（ark_stream.py:128-129 + assistant.py:448, 476-477, 486-502, 651），而 1.6C /query 仍丢（api/rag.py:130 不带 return_usage，RAGQueryResponse 无 usage 字段，models/rag.py:39-44），embedding 侧仍丢（vector_store.py:87-103 未抓 resp.usage）。**半落地结论：流式链路修好，1.6C 端点与 embedding 侧未修**——1.6C 端与向量侧拿不到真实 token 数与成本。
4. **降级标记透传**：assistant.py:26-28 注释声明 `DEGRADED_VECTOR/DEGRADED_BM25`「供 done/boundary 事件透传 degraded 语义」；实际 `recall` 返回 `degraded` 列表但 `pipeline_events` 未把它放进 rerank/done 事件（613, 650-652）。**翻转结论：方案有/代码无**——降级标记定义了但没进 SSE 事件，前端无法识别「本轮是降级回答」。
5. **降级矩阵**：完善文档 06「多路召回本身就是降级备份（向量挂→纯 BM25）；生成失败 → 预写答案兜底；全挂 → 边界话术」；代码中向量挂→纯 BM25（api/rag.py:97-106）、生成挂→召回清单（129-135）、全挂→拒答话术（120-126）均落地。**落地结论：降级矩阵按设计落地**，三类外部依赖故障都有稳定兜底。
6. **边界原则三则**：完善文档 09「语料没覆盖→拒答不编造 / 生成失败→references 当答案不空答 / 全挂→边界话术兜底」；1.6C 三则全落地，白盒链路用 BOUNDARY_MSG + GEN_*_MSG 各自落地。**落地结论：边界三则全部落地**，两条链路各自实现同一套边界原则。
7. **两道门**：语雀-问题4「权限门(前置)+范围门(后置)」；权限门=`verify_internal_token`（chat.py:27-35，Java 网关产 permission，Python 从 intent 开始），范围门=白盒 A9（0.75/0.5）。**权限门落地 / 范围门仅白盒**——权限门真实生效，范围门只在白盒链路生效（见第 1 条）。
8. **评测边界拒答 0 token**：eval_agent.py:33-34 注释「断言=触发固定话术+0 token」；`_boundary_trace` 0 token、不进 generate、score 5/0。**落地结论：评测边界拒答 0 token 按设计落地**，边界用例不产生 LLM 成本。

> 证据：详见 `3.代码/分析-07-API降级与容错.md`（§隐性坑 / §对账要点）
