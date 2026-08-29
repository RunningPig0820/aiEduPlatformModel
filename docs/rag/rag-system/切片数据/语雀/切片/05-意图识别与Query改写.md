# 意图识别与Query改写

> summary: 意图识别与Query改写
> 权威度: 0.8
> 模块: rag-system
> COS路径: rag-slices/rag-system/语雀/05-意图识别与Query改写.md
> 类别：架构设计

---

> 检索摘要：意图识别怎么实现？LLM 结构化输出 + 规则兜底怎么配合？输出哪些字段（anchor/category/ambiguous/candidates）？clarify 澄清和 switch 切换什么时候触发？Query 改写怎么透传？问候/寒暄怎么识别？

### 核心术语

| 术语 | 定义 |
|---|---|
| 意图硬路由 | 架构/代码/部署/评测/接口→RAG项目；禁区模块→固定拒答 |

### 意图识别（intent）

intent 为 LLM 结构化输出 + 规则兜底：模块锚点 anchor、类别 category、switch 判定 switchDetected、指代不明 ambiguous、候选 candidates、锁定节 lockedSections；LLM 失败回退关键词锚定（degraded 走 200）。

【已定 08-25】意图识别层 = **LLM 结构化输出 + 关键词兜底**（`{anchor, category, switch_detected, ambiguous, candidates}`，失败回退 `_fallback_anchor`/`_deictic_anchor`，degraded 走 200）。证据：design-java D2；spec-pipeline。

### 语义分析层透传 3 项

语义分析层透传 3 项：原始问题 / 改写后问题 / 意图分类标签（如 `#rag_project` 或 `#reject`）。证据：语雀-原文件-问题8.md。

### 硬路由

凡问题涉及"系统架构 / 代码实现 / 部署流程 / 评测方案 / 接口设计"→ 强制路由至 **RAG项目** 知识库。证据：语雀-原文件-问题8.md。

### SSE 事件：intent / clarify / switch

| 事件 | 内容 | 条件 |
|---|---|---|
| intent | LLM 结构化：anchor/category/switchDetected/ambiguous/candidates/lockedSections；问候→category="问候" | 可含 degraded（LLM 失败回退关键词锚定） |
| clarify | 固定话术 + candidates(字符串 id 数组) + default，0 token 不计答案轮次、写 history | ambiguous & candidates≥2；点选候选 = 重发原问 + currentProject=点选 id（intent 以 currentProject 为权威锚点） |
| switch | fromAnchor→toAnchor，上下文重置（仅下一 turn，不掐在途流） | 前端 current_project ≠ 会话已锚定 project |

分支无流规则：`clarify`/`switch` 分支**无 rewrite/recall/generate**。时序冻结为 `permission → intent → (clarify|switch) → rewrite → rerank → (boundary|token) → done`，不得重排/丢失。证据：语雀-原文件-问题9.md；design-java 契约 D-A~D-E + 事件时序（M2 冻结）。

### Query 改写（rewrite）

改写后问题透传前端 `{originalQuestion, rewrittenQuery}`（基于原问题+锚点+历史）。证据：语雀-原文件-问题8.md；spec-pipeline。

### 问候识别与欢迎引导（D-E）

【定稿 D-E】intent 将"你好/Hi/在吗"识别为 `category="问候"`、`ambiguous=false`，**不触发 clarify**（clarify 仅用于功能指代不明：ambiguous+candidates≥2；实联调发现"你好"被误判 ambiguous 弹澄清很怪）；走**欢迎话术 + 引导池建议**（0 生成 token，不 recall 不 generate），指向 ①项目介绍②操作③数据关联④难点。代码实现 `is_greeting` 关键词预检（你好/您好/hello/hi/哈喽/嗨/hey/在吗，**短句 ≤8 字才命中防误杀**，assistant.py:361,366-372）+ `WELCOME_MSG` 直返 done（assistant.py:580-586）。证据：design-java D-E；分析-05。

### 兜底（建议 #2）

intent 结构化输出兜底——复用 200 + degraded=true 惯例：LLM 失败→回退规则（现有 `_fallback_anchor` 已写该兜底）。

---

> 检索摘要（选型合并）："意图识别为什么用 LLM 结构化 + 规则兜底？问候语怎么处理？"——选型拍板：LLM 结构化输出 {anchor, category, switch_detected, ambiguous, candidates}（0 温度、关思考、20s 超时）+ 关键词规则兜底（_fallback_module/_fallback_anchor）+ 指代词兜底（_deictic_anchor），失败 degraded 走 200 不阻断链路；否决纯规则（"语义分析"是假的、白盒露怯）与纯 LLM 无兜底（挂了链路全断）。问候/寒暄识别 category="问候"、ambiguous=false 不触发 clarify，走欢迎话术 + 引导池建议 0 token 不 recall 不 generate（否决问候走普通 intent——误判 ambiguous 弹澄清很怪）。

### 选型17：意图识别实现选型
> 检索摘要：意图识别用 LLM 结构化输出 {anchor, category, switch_detected, ambiguous, candidates} + 关键词规则兜底（_fallback_anchor），失败 degraded 走 200 不阻断链路；否决纯规则（"语义分析"是假的、白盒露怯）与纯 LLM 无兜底（挂了链路全断）。

- 选型场景：意图识别层用纯规则还是 LLM（白盒"意图"阶段真实性）
- 候选方案A：纯规则硬路由
  - 方案A优劣（致命短板）：零成本、确定性；但"语义分析"是假的，白盒展示"意图识别"阶段露怯，面试问"这个阶段在干嘛"答不上真实语义。
- 候选方案B：LLM 结构化输出 + 规则兜底
  - 方案B优劣：intent 每轮开头非流式快模型（0 温度、关思考、20s 超时）输出闭集元数据 `{anchor, category, switch_detected, ambiguous, candidates}`；失败/超时/非闭集 → 回退关键词锚定（`_fallback_module` + `_fallback_anchor`）+ 指代词兜底（`_deictic_anchor`），degraded 标记走 200 不阻断链路；语义与成本平衡。
- 候选方案C：纯 LLM 无兜底
  - 方案C优劣（致命短板）：语义最强；但挂了链路全断，白盒整轮不可用。
- 最终拍板：LLM 结构化输出 + 关键词规则兜底（D2）
- 拍板理由：白盒展示"语义分析"必须真实发生；LLM 判意图 + 关键词兜底 = 语义与成本平衡，接口返回结构固定（`{locked_sections, strategy}` → 扩展为 `{anchor, category, switch, ambiguous, candidates, lockedSections}`），检索/生成只消费结果。
- 落地对账：落地——`_INTENT_SYSTEM` 输出五字段（`query.py:139-187`）→ `_sanitize_intent` schema 校验（`query.py:190-214`）→ 失败回退模块关键词 `_fallback_module` + 节关键词 `_fallback_anchor`（`query.py:118-135`）→ 指代词兜底 `_deictic_anchor`（`query.py:275-290`）；LLM 失败 intent 事件带 degraded 走 200；两层锚定：anchor=模块级（选语料池）+ locked_sections=节级（加权 ×1.5，白盒链路写死 `locked_sections=[]` 被旁路，`assistant.py:118`）。结论=落地。

### 选型20：问候处理选型
> 检索摘要：问候/寒暄（你好/Hi/在吗）识别为 category="问候"、ambiguous=false，不触发 clarify（实联调发现"你好"误判 ambiguous 弹澄清很怪），走欢迎话术 + 引导池建议，0 生成 token、不 recall 不 generate。

- 选型场景：用户发问候语走普通 intent 链路（clarify 澄清）还是独立欢迎路径
- 候选方案A：当普通 intent 走（问候误判 ambiguous → 弹澄清）
  - 方案A优劣（致命短板）："你好"被误判 ambiguous、candidates≥2 → 弹功能澄清框很怪，浪费一轮、体验断裂；问候不是功能指代不明，语义上不该走 clarify。
- 候选方案B：独立欢迎引导（0 token）
  - 方案B优劣：`is_greeting` 关键词预检（你好/您好/hello/hi/哈喽/嗨/hey/在吗，短句 ≤8 字才命中防误杀，`assistant.py:361,366-372`）+ `WELCOME_MSG` 直返 done（`assistant.py:580-586`），带引导池建议（指向 ①项目介绍②操作③数据关联④难点），不 recall 不 generate，0 生成 token。
- 最终拍板：独立欢迎引导（D-E）
- 拍板理由：产品校准——问候语 `ambiguous=false` 不触发 clarify（clarify 仅用于功能指代不明：ambiguous+candidates≥2）；走固定欢迎话术 + 引导池建议（0 生成 token，复用 guide 静态池）。
- 落地对账：落地——`is_greeting` 关键词预检（短句 ≤8 字防误杀）+ `WELCOME_MSG` + `_spread_pool_suggestions`（`assistant.py:375-380, 583-586`），0 token 直接 done。结论=落地。

> 证据：详见 `1.语雀/语雀-方案选型对比.md`（§选型17/20）｜ 语雀-决策记录.md D2/D18/D-E ｜ 代码分析 分析-01~09
