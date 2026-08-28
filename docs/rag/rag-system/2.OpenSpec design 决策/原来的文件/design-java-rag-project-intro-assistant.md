## Context

面向学生的**RAG 项目介绍助手**（`rag-project-intro-assistant`）：学生可在项目页面内就本项目设计逻辑提问（项目介绍 / 操作流程 / 数据关联 / 难点），回答遵循 RAG 标准链路并把中间状态白盒透传前端。这不是纯 RAG——产品是"讲清项目"，RAG 是证明能力的引擎。

现状约束与可复用资产：
- **Python 侧已有单模块 RAG 链路**：`ai-edu-ai-service/core/rag/query.py` 已实现 `classify(LLM→关键词兜底)` → `retrieve_vector(COS)` + `retrieve_bm25(本地jsonl)` → `orchestrate(RRF×authority×锚定)` → `generate(doubao)`，含 `references`（file/file_path/anchor/authority/summary）、usage 统计、降级链（向量挂→纯BM25；doubao挂→返回召回块；置信度低→拒答）。语料 `scripts/rag/data/rag_slices.jsonl`（234 块）为 **AI答疑模块唯一已切片入库数据**。
- **评估链已存在**：`run_eval.py`（CLI/API，`--compare` 版本对比）→ `eval_agent.py`（`hit_at_k`/`judge_quality`/`calc_cost`/`aggregate`）→ `eval_dataset.py`（格式校验，5 类型闭集，每模块 ≥5 条）。已有 baseline 报告：hit@3=0.80、质量分=4.2/5、耗时≈5.6s、成本≈¥0.016。
- **tutoring 两段式可复用**：Java 网关编排（安全预检→组装上下文→Python decide 非流式→护栏→generate 流式 SSE 透传）已验证；`SseMetaDTO`/`SseMasterySignalDTO` 事件 DTO、snake↔camel 契约纪律（`@JsonProperty`、`FAIL_ON_UNKNOWN_PROPERTIES=false`、degraded 走 200 不走 503）均为既有约定。
- **前端**：学生已有 AI答疑页（AiQa.jsx）与相关 hooks，RAG 助手前端另立变更，本设计只定后端契约。

定位说明：本变更与 Model 仓库 08-21 `project-intro-rag` 设计**方向不同**——后者是面试官 demo、覆盖 4 业务页、`role` 走 body；本变更是**学生**、仅讲 RAG 项目自身（AI答疑模块有语料）、角色走可信 session。**实现上泛化已有 `/api/tutoring/rag/query`，不照搬 08-21 的双池 QA 设计**（保留其"范围门=检索置信度"与"预写答案兜底"思想）。

## Goals / Non-Goals

**Goals:**
- 白盒 RAG 链路：权限 → 意图 → 改写 → 多路召回 → RRF 重排 → 生成，全阶段 SSE 事件透传前端。
- 角色硬门：仅 STUDENT 放行，非学生/角色缺失 → 固定 403，不进 RAG 流程、0 token。
- 模块全放行 + 低置信度过滤：AI答疑/知识图谱/题型分析/RAG 四模块均可路由，无禁区硬拒答；查不到关联文档 → 范围门低置信度过滤（固定话术，付 recall 省 generate），唯一拒答路径为 `boundary`（reason=low_confidence）。
- clarify 澄清轮：歧义（多候选功能）→ 固定澄清话术 + 默认当前功能，最多一轮，不计答案轮次。
- 引用透明：仅回传 RRF 精排 Top-K 块（标题/摘要/file_path），`is_quoted` 用 LCS 硬匹配（8 中/12 英），非 LLM 自述，`done` 后补发。
- 健壮性：召回 2s / 生成 8s 分层超时，`is_disconnected()` 断连取消，超时降级话术写死（0 token）。
- 计费透明：tokens_usage `{prompt, completion, cache_hit, total}` + `trace_id`，供前端断线补查；会话累计 token（关闭对话时返回）。
- 显式关闭对话：学生可在对话中主动结束会话（中止在途流 + 会话置关闭 + 返回会话累计 token），区别于断连取消。
- 引导：完成后运行时 LLM 生成建议（1~3 条，向 ①项目介绍 ②操作 ③数据关联 ④难点 引导）。
- 评估复用：`run_eval.py` 链 + 新增 `边界拒答` 类型 + `precision_at_k` + is_quoted 校验 + baseline 报告白盒展示。

**Non-Goals:**
- **不做生成中切换**：切换只发生在下一轮 intent（`switch_detected`），生成中前端断开只走 `is_disconnected()` 取消，不做服务端主动掐流（半截 token 白烧 + 上游取消不可靠）。
- **不做教育内容检索**（知识点/题库/答疑学科题）——语料是本项目方案文档，不是教育数据。
- **不做图谱检索召回**（不接 Neo4j）——召回对象是文档（向量+BM25）。
- **不接真实权限体系扩展**——本期仅学生角色，非学生固定 403。
- **不实现 mermaid 动态生成**——本期不做流程图预置/渲染（前端另立变更，可后续补）。
- **不实现前端**——仅定后端契约与 SSE 事件格式。
- **不做生产级部署与鉴权扩展**——沿用 `x-internal-token` 内部调用。

## Decisions

### D1. 角色门在 Java（可信 session），不在 Python，禁信 body
学生登录后 session 含 `userId`+角色；Java 网关从 `HttpSession.getAttribute("role")`（或网关 Header）取角色，`STUDENT` 才放行，否则固定 403 响应体（非 RAG 流程、不调 LLM、不落任何 trace）。前端任何 body 传 role 一律忽略。
- **为什么**：与 tutoring 认证桥接（方案 A）一致——前端走 Java 网关，Python 不自己认证、不碰会话；严禁信任前端传参（spec 硬性要求）。
- **备选**：Python 自校验 → 破坏"Python 无状态"边界，弃。

### D2. 意图识别用 LLM 结构化输出 + 规则兜底，输出 `{anchor, category, switch_detected, ambiguous, candidates}`
intent 为每轮开头的**非流式**调用（快模型、0 温度、关思考），输出闭集元数据。失败/超时/非闭集 → 回退关键词锚定（复用 `_fallback_anchor` + `ANCHOR_RULES`），degraded 标记走 200。
- **两层锚定（Python 侧校准确认）**：`anchor` 是**模块级**（路由层，决定从哪个语料池召回）；`locked_sections`（节级，既有语义，如 04-安全/07-流式）保留为**加权层**（池内 authority × 节锚定精化）。两层并存、不是替换：orchestrate 的节级锚定加权**逻辑不改**，只新增 recall 前置"按 anchor 选语料池"（corpus 参数）。anchor 明确 → 单池召回 + 池内节加权；anchor 缺失/ambiguous → 维持现状（跨池或先 clarify）。
- **candidates（歧义候选模块）**：`ambiguous=true` 时 LLM 直接输出候选模块闭集（2~4 个，主源）；LLM 未给/给 <2 → 取会话最近 N 轮锚过的模块去重填充（兜底）；仍 <2 → 不触发 clarify，走默认 current_project。为 clarify 判定（D5）提供确定性输入。
- **为什么**：白盒展示"语义分析"必须真实发生；LLM 判意图类别（复用 `_CLASSIFY_SYSTEM` 的闭集分类）+ 关键词兜底 = 语义与成本平衡。接口返回结构固定（`{locked_sections, strategy}` → 扩展为 `{anchor, category, switch, ambiguous, candidates, lockedSections}`），检索/生成只消费结果。
- **备选**：纯规则 → 零成本但"语义分析"是假的，白盒露怯；纯 LLM 无兜底 → 挂了链路全断。

### D3. 切换判定收敛在下一轮 intent，服务端不做生成中切换
`switch_detected = (前端 current_project ≠ 会话已锚定 project) 或 (问题明确指向另一有语料模块)`。检测到 → 发 `switch` 事件 + 重置上下文（锚点/召回/轮次计数），走新锚点 rewrite→recall→generate。**不掐断任何在途流**——在途流要么完成、要么被 is_disconnected 取消。
- **为什么**：生成中切换 = ①中止上游 doubao HTTP 流（不可靠）②半截 token 已计费 ③前端打断渲染，三重代价，且学生真实动作只有"等完再问"或"关 fetch 再问"。tutoring 换题判定收敛 Java 的教训（换题判定在 Python decide、Java 只认 switch 事件）同构。
- **备选**：生成中服务端掐流 → 复杂 + 烧钱 + 打断感，弃（用户确认）。

### D4. 模块全放行 + 范围门低置信度过滤（唯一拒答路径）
- **放行**：AI答疑/知识图谱/题型分析/RAG 四模块**全部可路由**，意图层**无禁区硬拒答**（用户确认："AI答疑、知识图谱、题型分析和RAG模块都放行，当查询不到关联文档就直接返回可信度低过滤"）。
- **范围门**（recall 后，唯一拒答机制）：RRF 精排 top-K 综合分低于阈值（索引层 0.75 / 源文档池 0.5，沿用）→ 固定话术"未找到关联文档，我尚未掌握"，事件 `event: boundary, reason: low_confidence`，付了 recall 省 generate。
- **硬路由**：涉及"系统架构/代码实现/部署流程/评测方案/接口设计" → 强制路由至 RAG 项目知识库。
- **为什么**：语料即边界，查不到=低置信过滤，无需维护禁区模块列表；未来模块入库切片即自动可答（数据驱动，无代码改动）。话术写死 0 token。
- **备选**：意图门硬拒答禁区 → 需维护禁区列表、与语料现状耦合，弃。

### D5. clarify 澄清轮：歧义才问，默认当前功能，最多一轮
`ambiguous=true` 且 `candidates ≥ 2`（多候选功能）→ 发 `event: clarify`（固定话术模板 + candidates + default），**0 token 生成、不计答案轮次、写 history**。学生下一条重跑 intent；仍模糊（"就那个嘛"）→ 不再 clarify，直接默认当前功能继续。`default` 绑定源优先级：前端 `current_project` > 会话最后成功锚定功能。
- **候选判定输入（Python 侧校准确认）**：`candidates` 来源 = ① intent LLM 结构化输出直接给出（`ambiguous=true` 时输出候选模块闭集 2~4 个，主源，能"读懂"问题里的功能指代）→ ② LLM 未给/给 <2 → 会话最近 N 轮锚过的模块去重填充（兜底）→ ③ 仍 <2 → 不触发 clarify，直接走默认。`candidates` 是**模块级**（非节级），与 D2 的模块 anchor 同一闭集。
- **点选交互定稿（前端校准确认）**：学生点选候选 chip 后，前端**重发原问题 + `current_project=点选模块`**（非发裸功能名）——复用 Q2 已确认的"每次带 current_project 锚点"机制，intent 以 `current_project` 为**权威消歧锚点**直接锚定（不依赖 LLM 从功能名猜），原问保留供改写/召回；点选模块与会话锚点不同 → `switch` 事件照常触发（前端可提示"已切换至 X"）。
- **为什么**：低摩擦引导（单一候选直接走不问），防死循环（最多一轮），降本（写死话术）。spec 第 6 条"题型引导"的歧义场景正是"切换功能后问'这个功能怎么流转'"。
- **备选**：不问直接默认 → 答错功能体验更差；无限追问 → 死循环。

### D6. is_quoted 用 LCS 硬匹配，`done` 后补发，非 LLM 自述
生成完成后，遍历每个精排块的 `text`/`summary`，与最终 answer 做最长公共子串匹配，任意**连续 8 中文字符（或 12 英文字符）**命中 → `is_quoted=true`。前端 `rerank` 先发块（灰显），`done` 补 `quoted_keys`（高亮）。
- **为什么**：引用判定不依赖 LLM 主观自述（spec 硬性要求确定性），纯函数可单测可入评估。8 中文字符窗口对单 token chunk 不友好 → 生成完才匹配，故 `done` 后置补发。
- **风险（Python 侧校准）**：doubao 生成可能改写用词（如"类型先行流式"→"type先行"），导致 8 字符窗口**漏判**。→ 窗口大小可调（`config/settings.py`）；评估集加"改写答案"用例验证窗口够不够；漏判时块灰显但答案仍完整（非致命，前端无需报错）。
- **备选**：LLM 自报引用 → 不可靠；流中实时匹配 → chunk 粒度导致匹配窗口撕裂。

### D7. 分层超时 + 断连取消，降级话术写死
- 召回层：向量/Bm25 单路各 2s 硬超时，超时 → 降级为纯另一路（`{hits:[], confidence:0}` 冒泡捕获，复用 1.6C 语义）。
- 生成层：8s 硬超时 → **不走 LLM**，直接返回召回清单 + 固定话术"我找到了以下相关资料，但生成完整答案超时了，您可以直接点击查看原文：块1、块2、块3"。
- 断连：SSE 生成循环监听 `request.is_disconnected()`，断开 → 中止上游 doubao 流。
- **为什么**：分层超时是工程底线（spec 第 7 条）；超时降级话术写死成本 0，且用户拿到原始资料体验正向（非报错）。
- **备选**：统一 20s 超时 → 学生等待过久；生成超时也调 LLM 重试 → 重复花钱。

### D8. tokens_usage + trace_id
`done` 事件携带 `tokens_usage{prompt_tokens, completion_tokens, cache_hit_tokens, total_tokens}` + `trace_id`。usage 取流结束 ark 返回（`include_usage`）；cache_hit 取不到 → tokenizer 估算标注"估算"。`trace_id` 由 Java 生成透传 Python（同源贯穿日志，Python done 回显），供前端 `GET /api/rag/assistant/turns/{trace_id}` 断线补查。**history 由前端传**（方案 A，2026-08-26：最近 3 轮 `{question, answer, anchor}`，追问展开用——省略主语的"能说的详细一点吗"靠 history 还原，Java 透传 Python 只消费；不落库，刷新后为空=新会话）；**turns 只存 Java Redis**（每轮 done 按 trace_id 落 `rag:assistant:trace:{traceId}` TTL 24h，补查读 Redis；Python 不落会话 trace）。
- **为什么**：spec 第 8 条透明计费；tutoring 已改 ark_stream 取 usage，复用。cache_hit 是 doubao prompt 缓存命中计数，用于成本叙事。**history 方案 A（前端传）**：用户确认"不要落库"——前端本就持有每轮 {question, answer, anchor}，随 ask 回传即可，Java 不存 session 历史；刷新后前端消息清空则 history 空=新会话（可接受）。turns/trace 归 Java（每轮过手 done，天然聚合点），Python 保持无状态。
- **备选**：不补查接口 → trace_id 是死口（spec 要求"供断线后补查"）；Python 落 trace JSONL → 破坏无状态边界，弃。

### D9. 模块可用性数据驱动：四模块放行，无语料自然低置信过滤
知识库按模块组织；`rag_slices.jsonl`（AI答疑）现状。其它模块语料不存在时，提问**正常进入召回**但命中为空/低置信 → 范围门低置信度过滤（固定话术），不是意图层拒答。未来某模块入库切片 → 自动可答（**无需改代码**）。
- **为什么**：用户确认"四个模块都放行，查不到关联文档直接返回可信度低过滤；语料后面会补充"。语料即边界，无禁区列表。
- **备选**：硬编码 4 模块白名单 / 意图门拒答 → 与语料现状耦合，弃。

### D10. 评估复用 run_eval 链 + 三处扩展
- `eval_dataset.py` `VALID_TYPES` 增加 `边界拒答`；`expected` 断言 = "必须触发固定话术且不产生 token 流"。
- `eval_agent.py` 新增 `precision_at_k`（召回 top-k 中相关块占比，纯函数）；`judge_quality` prompt 升级原子声明模式（RAGAS Faithfulness 思想）可选。
- 新增 is_quoted 纯函数 `lcs_quote_match` 单测 + 入评估（`quoted_keys ⊆ 召回块`）。
- baseline 报告经 `GET /api/rag/assistant/eval/report` 白盒展示（hit@k/质量分/成本/耗时）。
- **为什么**："证明有效"不能靠感觉（用户明确要求可量化/可复现/可追溯）；现有链完整可复用，只需扩展。
- **备选**：重新造评估轮 → 重复建设。

### D11. 问题提示 = 开始引导 + 结束引导，底座池驱动，RAG 始终带上
**RAG 的特殊性**：AI答疑/知识图谱/题型分析是"展示页模块"（学生能导航到），RAG **不是展示页——它是始终在底层运行的引擎**，每轮答案都由它产出。所以问题提示不能把 RAG 当四个并列模块之一，**每次必须带上**（用户确认："每次问题提示的时候都需要把 RAG 带上"）。

**底座池（唯一引导来源，对齐 known-issues 问题6）**：每个模块一个 `{direction: [问题]}` 底座池（`ai-tutoring` 已由 Python 产出，来源 `docs/rag/ai-tutoring/7. 引导问题/引导问题.md`——随切片迭代持续更新，当前约 90 题；后续知识图谱/题型分析/rag-system 语料就绪后各加一个模块条目）。开始/结束引导都**以池为唯一来源**，问题必须对齐语料、保证每个都能答。
- **开始引导**（会话入口，未提问前）：从模块池取 3 条（**必含 ≥1 条 RAG 方向**，D11 常驻），0 token；走非 SSE 接口 `GET /api/rag/assistant/guide?currentProject=模块`——**前端必传当前功能模块**（每个功能的引导问题不同，进页面/切换功能时以当前功能为准），Java 透传 Python，缺省兜底 ai-tutoring（仅防御）。前端进入页面拉取一次，**不占冻结的 SSE 时序**。会话开始无上下文，LLM 无从生成，池即最优。
- **结束引导**（每轮 done 后）：运行时 LLM 生成 1~3 条建议（向 ①项目介绍 ②操作 ③数据关联 ④难点），**提示词注入池内问题作「可提问范围」硬约束——只能生成与池内方向类似的问题，不得自由发挥超出池子**；**必含 ≥1 条 RAG 方向**（把话题带回 RAG）；`completion_tokens` 计入本轮 `tokens_usage`。
- **池内兜底**：LLM 失败 / 输出形状异常 → **从池内随机抽 2~3 条**（必含 ≥1 条 RAG 方向），不再自由发挥。
- **为什么**：用户确认"引导建议不能让问题太自由，不然我也回答不好，所有 LLM 的问题也都必须根据池内问题问类似的"——自由生成的建议很多在语料里无对应切片（known-issues 问题6），学生点了答不上；池内出题保证可答、且把学生带到 ①②③④ 高频方向。
- **备选**：suggestions 纯 LLM 自由发挥 → 可答性无保障，问题6 已证明体验断裂，弃。

### D12. 显式关闭对话（close）+ 会话累计 token
学生可在对话中主动"结束对话"：`POST /api/rag/assistant/sessions/{sessionId}/close`（角色门同上，仅 STUDENT）。close 语义：
- **中止在途流**：若该 session 当前有生成流，中止上游 doubao（同 is_disconnected 取消），前端可关连接。
- **结束会话**：session 状态置 closed（Redis），后续同 session_id 的 ask → 固定话术"本轮对话已结束，可开启新对话"，不进入 RAG 流程、0 token。
- **返回会话累计 token**：Java 每轮 `done` 后将 `tokens_usage` 累加进 Redis（`rag:assistant:session:{sessionId}:usage`，TTL 24h 对齐 tutoring）；close 时读回返回 `{prompt/completion/cache_hit/total}` 会话累计值 + 轮数。**这补上 spec 第 4 条"对话消耗总 token"的缺口**（原来只有每轮）。
- **为什么**：显式 close 与断连取消是两件事——断连是异常路径（仅中止流），close 是学生主动结束（结束会话 + 结算）。累计 token 放 Java（每轮都经过它，天然聚合点），Python 保持无状态。
- **备选**：close 仅前端清空 UI 不发后端 → 无法结算累计 token、session 状态残留；累计 token 放 Python → 破坏无状态边界。

### 定稿契约对齐（2026-08-25 三端：前端/Python/Java）

**D-A. 模块 id 闭集（三端统一）**
闭集 = `ai-tutoring`（AI答疑）/ `knowledge-graph`（知识图谱）/ `question-analysis`（题型分析）/ `rag-system`（RAG 项目）。**弃用** `rag-project`、`question-type`。语料选池按块级 metadata `tags.module == anchor` 过滤（**不依赖目录同名**）；`slice_corpus` 的 module 参数化（不再硬编码）。clarify `candidates` 为**字符串 id 数组**，中文 label 由前端 `pageModuleMap` 维护（Python 不产 label、契约零改动），点选候选以 id 作 `currentProject` 重发原问。

**D-B. permission 携带 trace_id**
`permission` 事件 = `{role, allowed, traceId}`；trace_id 由 Java 网关入口生成，流一开始前端即可取（断线补查**不依赖 done**）。Python 无感（不产 permission）。

**D-C. sessionId 由前端生成**
前端面板挂载生成 UUID（复用 `generateSessionId` 模式）整场复用；Java 以 sessionId 为键累计 token；ask 未知 session 按新会话（累计从 0），close 未知 session → 10002。

**D-D. 查看原文走 Java 代理**
新增 `GET /api/rag/assistant/source?path=<urlencoded>`（STUDENT 角色门）转发 Python `/api/rag/source/{file_path}`；Python 保留挂载作转发目标，前端**不直连 Python**。file_path 走 query 传参（不走 path，避免特殊字符被容器拒）。

**D-E. 问候识别与欢迎引导（2026-08-25 产品校准）**
intent SHALL 识别"问候/寒暄"（如"你好/Hi/在吗"）为 `category="问候"`、`ambiguous=false`——**不触发 clarify**（clarify 仅用于功能指代不明：ambiguous+candidates≥2，**不用于问候语**，实联调发现"你好"被误判 ambiguous 弹澄清很怪）。问候语 SHALL 走**欢迎引导路径**：不 recall 不 generate（省 token），直接返回**固定欢迎话术 + 引导建议**（指向 ①项目介绍②操作③数据关联④难点，复用 guide 静态池，0 生成 token）。

### 交付编排（并入自 rag-assistant-incremental-delivery，2026-08-25 归档）

**M1-M8 里程碑纵向切片**：每个里程碑 = 纵向切片 + 前后端+模型端**三端对接测试**（完成即联调，问题早暴露）。M 编号即构建顺序，依赖单向（M(n) 只依赖 ≤M(n-1) 产出）。

**桩替策略**：上游未完成阶段先返回固定占位（M2/M3 的 generate 桩替），使整轮可通、前端不被下游阻塞；M4 起移除桩替接真实。

**完成标准**：每里程碑完成 = **前端可见物** + **对接测试用例全绿**（见 test.md 里程碑门禁映射表 2A）。

**对接节奏**：每里程碑后端+Python 合并该切片 → 前端对接该切片可见物 → 跑该里程碑门禁用例全绿才进入下一步。**SSE 契约 M2 冻结，下游只补字段不重排**。

**原 7 项清单归属**：权限判断→M1、意图分析→M2(+改写/switch/SSE骨架)、多路召回+remark打分+边界→M3、生成+token展示→M4、自我检查→M5、问题提示→M6、会话收尾→M7；缺口(rewrite/clarify/范围门/switch/close+累计token/补查/超时断连/SSE骨架/评估/问候欢迎)均落到对应里程碑。

## Risks / Trade-offs

- [intent LLM 偶发误判] → 规则兜底（`_fallback_anchor`）+ degraded 标记走 200；评估集 `边界拒答` 类型覆盖误判回归。
- [is_quoted 匹配 8 中字符过于严格/宽松] → 参数可调（`config/settings.py`）；入评估校验 quoted_keys ⊆ 召回块；前端灰显/高亮兜底。
- [cache_hit_tokens 拿不到] → tokenizer 估算 + 标注"估算"（08-21 已留口子）。
- [运行时 suggestions 增加成本] → 计入本轮 usage 展示；LLM 失败静态池兜底；可配置开关关闭。
- [多模块语料缺失导致可答面窄] → 数据驱动，先 AI答疑；未来入库即自动放行，验收按"链路真实完整"讲。
- [跨项目问题（AI答疑页问知识图谱）在无语料模块下低置信过滤] → 明确为预期行为（范围门 low_confidence），评估集覆盖。
- [上下文窗口截断丢上下文] → 保留最近 3 轮 + 锚点由 session 独立携带，前端可见截断提示（如需）。
- [SSE 事件时序被前端依赖] → 冻结契约：`permission → intent → (clarify|switch) → rewrite → rerank → token → done`，不得重排/丢失（沿用 tutoring 阶段二契约冻结纪律）。
- [流式 usage 只在结尾返回] → done 才更新成本展示（面试/汇报可讲这个坑）。

## Migration Plan

1. **Python 先行**（Model 仓库，对应其 `rag-project-intro-assistant-python` 变更）：泛化 `core/rag/query.py` 为白盒链路（intent/rewrite/recall/rerank/generate + clarify/is_quoted/分层超时/suggestions），新增 `/api/rag/assistant/ask` SSE 端点，扩评估集。**不影响既有 `/api/tutoring/rag/query`**（独立路由）。
2. **Java 网关**：新增 `RagAssistantController`（角色门 + SSE 中继 + trace_id），复用 `LlmGateway` internalToken 调用。回滚 = 摘除路由，不影响 tutoring。
3. **前端**（另立变更）：学生侧 RAG 助手页消费白盒事件。
4. **数据**：AI答疑语料保持现状；其它模块语料后续入库即自动放行，无迁移。

## Open Questions

- intent LLM 类别闭集与 `locked_sections` 的映射是否沿用现有 `CATEGORY_SECTIONS`（项目介绍/操作/难点/数据关联/最危险），还是针对学生场景重构（spec 提到 ①②③④ 四方向）——建议沿用闭集，前端引导语对应即可。
- `cache_hit_tokens` 是否真由 doubao/ark 返回——需实现期实测，取不到按"估算"。
- 会话：**不做断线恢复**（仅 trace_id 单轮补查，用户确认）；**不设轮数上限**（用户确认轮数无意义），改为上下文窗口保留**最近 3 轮**（默认，可配）。窗口大小的最终值待定。
