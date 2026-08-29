# token成本与真算

> summary: token成本与真算
> 权威度: 0.8
> 模块: rag-system
> COS路径: rag-slices/rag-system/语雀/10-token成本与真算.md
> 类别：数据存储

---

> 检索摘要：token 怎么"真算"？为什么流式 usage 必须在结尾取、include_usage 不加就拿不到？丢 usage 的坑在哪两处？成本叙事怎么讲（本地bge免费+doubao单价）？cache_hit 取不到怎么办？为什么 glm-4-flash 免费叙事放弃了？

### token 真算（usage 流式结尾更新）

现有代码**丢 usage**的坑（已踩）：`ark_stream.py` 请求体没加 `stream_options: {"include_usage": true}`（OpenAI 兼容流式不加默认不返回 usage）；`_parse_sse_lines` 只解析 reasoning/content/tool_calls，流里带 usage 也被丢弃。修复 = 两处小改动：请求体加 `include_usage`、解析时抓最后一个 chunk（choices 为空但带顶层 usage）→ 流结束取 `usage.prompt_tokens / completion_tokens`。embedding 侧同理：`vector_store.embed()` 只返回向量，`resp.usage.total_tokens` 未抓。证据：语雀-原文件-问题4.md；design-python-project-intro-rag.md D7。面试可讲："流式下 usage 只在结尾返回，所以我是结束后更新"。

【落地对账】**白盒流式链路已修**：`stream_generate` 传 `include_usage=True`（`assistant.py:448`）+ 流末尾 usage chunk 经 `_parse_sse_lines` yield（`ark_stream.py:128-129`）+ `assemble_usage` 组装 `{prompt/completion/cache_hit/total}` 进 done.tokens_usage（`assistant.py:486-502, 514`，cache_hit 从 `prompt_tokens_details.cached_tokens` 取，取不到 → 0）；**评测侧真采**（`generate(return_usage=True)` → `eval_agent.calc_cost`）。**1.6C `/query` 端点仍不采**（`api/rag.py:130` 未传 `return_usage`，`RAGQueryResponse` 模型无 usage 字段）；**embedding 侧仍未抓**（`vector_store.embed()` 不返 usage，方案 D7"embedding 单列"未落地）。证据：分析-01/04/07。

### 成本叙事

- **每轮明细**：输入(query + 检索到的 N 段上下文共 X tokens) + 输出(答案 Y tokens) = Z tokens；可视化检索成本（"本轮检索了 3 段上下文 450 tokens"）让面试官直观看到 RAG 为什么费 token。
- **累计 + 费用换算**：整场会话累计 token，按模型单价换算成 ¥。
- **成本控制故事**：本地 bge 免费 embedding / top-K 限制上下文膨胀 / 查询 LRU 缓存 / 降级到关键词检索便宜路径 / history 截断（最近 3 轮）+ 0 token 兜底话术（问候/澄清/边界/超时均写死不调 LLM）。证据：语雀-原文件-问题3.md；分析-01/07。

### 模型选择与边际成本

| 方案 | 成本叙事 | 代价 |
|---|---|---|
| ~~免费模型 glm-4-flash~~ | ~~"本地 bge embedding + 免费生成模型，边际成本趋近 0"（最强）~~ | 08-25 已不采用 |
| **doubao（答疑同款）** | 复用 ark_stream（usage 改动只做一次）| token 单价付费，费用数字不好看 |

证据：语雀-原文件-问题5.md。08-21 生成选 doubao 流式；【已定 08-25】**生成/意图/改写/判分统一 doubao**（`doubao-seed-2-0-mini-260428`：意图/改写/判分 0 温度关思考 20s 超时、生成 0.2 温度 60s 超时，`settings.py:56,60`），**glm-4-flash 免费模型优先叙事已放弃**；成本叙事转为"本地 bge embedding 免费 + doubao 单价（¥0.003/0.009 千 token）+ top-K 控制上下文膨胀 + 0 token 兜底话术"。证据：分析-01/04/06。

### cache_hit_tokens 与估算口子

`cache_hit_tokens`（缓存命中）ark/doubao **不一定真返回**，取不到→ tokenizer 估算并标注"估算"（08-21 已留此口子）。【落地】代码从 `prompt_tokens_details.cached_tokens` 取（`assistant.py:486-502`），取不到**置 0 而非"估算"标注**；需实现期实测 doubao 是否真返回缓存命中计数。证据：语雀-原文件-问题8.md（待验证项）/ 问题11.md；分析-01。

### 数据结构

`tokens_usage`：`prompt_tokens / completion_tokens / cache_hit_tokens / total_tokens`，随每轮返回（done 事件）。证据：语雀-原文件-问题8.md。


---

> 检索摘要（选型合并）："token 消耗怎么算？为什么选 usage 真算？"——选型拍板：usage 真算（请求体加 stream_options.include_usage、解析结尾 usage chunk、流结束更新），拿不到 usage 时降级 tokenizer 估算并标注"估算"；成本是 RAG 最大实战痛点，真算+展示=成本控制叙事，流式 usage 只在结尾返回故"结束后更新"是踩过流式坑的加分细节；落地半覆盖——白盒流式链路与评测已真采，1.6C /query 端点与 embedding 侧未采。

### 选型9：token 统计选型
> 检索摘要：token 消耗采用 usage 真算（请求体加 stream_options.include_usage，解析结尾 usage chunk，流结束更新），拿不到 usage 时降级 tokenizer 估算并标注"估算"；代码白盒链路与评测已真采，1.6C 与 embedding 仍丢。

- 选型场景：token 成本展示怎么算——真算还是估算
- 候选方案A：usage 真算（流结束更新）
  - 方案A优劣：请求体加 stream_options={"include_usage": true}，解析最后一个 choices 为空但带顶层 usage 的 chunk，流结束时取 prompt/completion_tokens；embedding 侧抓 resp.usage.total_tokens；数据真实。
- 候选方案B：tokenizer 估算
  - 方案B优劣（致命短板）：实现简单；但只是估算，与真实计费有偏差，只能标注"估算"。
- 最终拍板：usage 真算（流结束更新）；拿不到 usage 时降级 tokenizer 估算并标注"估算"
- 拍板理由：成本是 RAG 最大实战痛点，真算+展示=成本控制叙事；流式 usage 只在结尾返回，所以"结束后更新"是踩过流式坑的加分细节（D7、问题3/4）；cache_hit_tokens 若 ark 不返回也走估算兜底（问题11 #7）。
- 落地对账：部分落地——**白盒流式链路已修**：`stream_generate` 传 `include_usage=True`（`assistant.py:448`）+ 流末尾 usage chunk 经 `_parse_sse_lines` yield（`ark_stream.py:128-129`）+ `assemble_usage` 组装 `{prompt/completion/cache_hit/total}` 进 done.tokens_usage（`assistant.py:486-502, 514`，cache_hit 从 `prompt_tokens_details.cached_tokens` 取、取不到→0）；**评测侧真采**（`generate(return_usage=True)`→`eval_agent.calc_cost`）；**1.6C `/query` 端点仍不采**（`api/rag.py:130` 未传 return_usage，`RAGQueryResponse` 无 usage 字段）；**embedding 侧仍未抓**（`vector_store.embed()` 不返 usage，方案 D7"embedding 单列"未落地）。结论=方案拍板成立，落地半覆盖。

> 证据：详见 `1.语雀/语雀-方案选型对比.md`（§选型9）｜ 语雀-决策记录.md D7/D19/D20 ｜ 代码分析 分析-01/04/07

---

## 决策记录 D# 合并（来源：语雀-决策记录.md）

### D19 token 真算：usage 流式结尾（include_usage + 结尾 chunk）
> 检索摘要：token 真算修复丢 usage 坑：ark_stream 请求体加 stream_options.include_usage，解析结尾 usage chunk（choices 空但顶层带 usage），流结束取 prompt/completion；embedding 侧抓 resp.usage.total_tokens 单列。

| 属性 | 内容 |
|---|---|
| 背景 | 现有代码丢 usage：ark_stream.py 请求体没加 stream_options.include_usage（OpenAI 兼容流式默认不返回 usage）；_parse_sse_lines 只解析 reasoning/content/tool_calls，流里带 usage 也被丢弃 |
| 演进 | 修复 = 请求体加 include_usage + 解析最后 chunk → 流结束更新本轮；embedding 侧 vector_store.embed() 抓 resp.usage.total_tokens |
| 拍板理由 | 成本是 RAG 最大实战痛点；真算 + 展示 = 成本控制叙事；流式 usage 只在结尾返回 → "结束后更新"（面试可讲这个坑） |
| 系统影响 | 【落地对账】白盒流式链路已修（stream_generate include_usage=True assistant.py:448 + _parse_sse_lines yield usage ark_stream.py:128-129 + assemble_usage 组装进 done.tokens_usage），评测侧真采（generate(return_usage=True)）；1.6C /query 端点仍不采（RAGQueryResponse 无 usage 字段）；embedding 侧仍未抓（vector_store.embed() 不返 usage） |
| 证据 | 语雀-原文件-问题4；design-python-project-intro-rag D7；[总揽§7.1]；分析-01/04/07 |

### D20 cache_hit_tokens 估算口子
> 检索摘要：cache_hit_tokens（缓存命中）ark/doubao 不一定真返回，取不到用 tokenizer 估算并标注"估算"（08-21 已留口子）；代码从 prompt_tokens_details.cached_tokens 取，取不到置 0。

| 属性 | 内容 |
|---|---|
| 背景 | doubao prompt 缓存命中计数用于成本叙事，但 ark/doubao 不一定真返回 |
| 演进 | 08-21 方案取不到 → tokenizer 估算 + 标注"估算" → 【落地】代码从 prompt_tokens_details.cached_tokens 取（assistant.py:486-502），取不到置 0 而非"估算"标注 |
| 拍板理由 | 缓存命中计数是成本叙事加分项，但拿不到不能编；留估算口子保诚实 |
| 系统影响 | 需实现期实测 doubao 是否真返回缓存命中计数（见 D42）；成本展示按"估算"口径 |
| 证据 | 语雀-原文件-问题8（待验证项）/问题11；[总揽§7.4]；分析-01 |

### D21 会话累计 token + close 结算（sessionId 前端 UUID）
> 检索摘要：Java 每轮 done 后将 tokens_usage 累加进 Redis，close 时读回返回会话累计 token+轮数；sessionId 由前端面板挂载生成 UUID 整场复用（D-C），ask 未知 session 按新会话。

| 属性 | 内容 |
|---|---|
| 背景 | 原来只有每轮 token，缺"对话消耗总 token"口径 |
| 演进 | 08-21 只每轮展示 → 08-25 close 显式结束会话 + 结算（补上总消耗缺口）；sessionId 前端生成（D-C） |
| 拍板理由 | close 显式结束（区别于断连取消）；累计 token 放 Java（每轮过手，天然聚合点），Python 无状态 |
| 系统影响 | 【落地】POST /api/rag/assistant/sessions/{sessionId}/close（中止在途流 + 置 closed + 返回累计 token/轮数）；Redis key rag:assistant:session:{sessionId}:usage TTL 24h；断连未 close 时累计保留续接；close 未知 session → 10002 |
| 证据 | 语雀-原文件-问题8；design-java D12/D-C；spec-java resilience；[总揽§4.4/§3.4] |

### D22 生成模型成本叙事：免费 glm-4-flash → doubao 统一
> 检索摘要：生成模型从"免费 glm-4-flash 边际成本趋近 0"叙事改为 08-25 统一 doubao（生成/意图/改写/判分同模型），成本叙事转为"本地 bge embedding 免费 + doubao 单价 + top-K 控上下文膨胀 + 0 token 兜底话术"。

| 属性 | 内容 |
|---|---|
| 背景 | 成本叙事需要选择生成模型与叙事口径 |
| 演进 | 08-21 生成选 doubao 流式 + 免费 glm-4-flash 优先叙事 → 【已定 08-25】生成/意图/改写/判分统一 doubao（doubao-seed-2-0-mini-260428：意图/改写/判分 0 温度关思考 20s 超时、生成 0.2 温度 60s 超时，settings.py:56,60），免费模型叙事放弃 |
| 拍板理由 | 复用 ark_stream（usage 改动只做一次）；与答疑同款能力一致；本地 bge embedding 免费 + top-K 控制上下文膨胀 + 0 token 兜底话术（问候/澄清/边界/超时均写死不调 LLM） |
| 系统影响 | 成本叙事：本地 bge embedding 免费 + doubao 单价（¥0.003/0.009 千 token）+ top-K 控制 + history 截断最近 3 轮 |
| 证据 | 语雀-原文件-问题5；[总揽§7.3]；分析-01/04/06 |

> 决策记录证据：语雀-决策记录.md §D19/D20/D21/D22
