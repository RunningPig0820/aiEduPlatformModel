# question-type-mastery-backend 技术设计

## Context

掌握度 = 题型 已确立（`kp-matching-lightup` 翻转），但数据底盘是零散观测：

- **信号形态**：`decide` 逐轮输出三档信号（mastered/practicing/struggling），`applyMasteryAndErrors` 取 **max 单调不减**（答错不降分，置信度视角）。算不出「练了几道、答对几道」的正确率。
- **题型名是 LLM 自由文本**：`t_student_topic_mastery` 的 key 是 `TopicKeyNormalizer.normalize(label)`（字符串级）。「一元二次方程」和「解一元二次方程」裂成两行。聚合 merge（kp_uri 重叠 ≥0.7）只影响题型库，**不回流掌握表**。
- **零题目状态**：后端明确不记录题目内容（`DecideContext` 注释），题目文本只存在于会话 history 里。
- **掌握信号唯一来源 = AI 答疑**（题型分析只记题目不产生对错）。
- **无题库、零锚点**：没有预置的题型分类表，canonical 由学生题目动态涌现（见 Decision 4）。
- **COS 向量检索无 Java SDK**：只有 Python/Go SDK（`CosVectorsClient`/`VectorService`），向量操作走 Python 桥（见 Decision 5）。

诉求（承接前端 `question-type-mastery`）：掌握度有题目证据、能算百分比、能追溯。掌握的是题型（解题模式）。

## Goals / Non-Goals

**Goals:**
- 建立「题目 → 题型掌握」完整数据底盘：采集 → 题型名归一 → 累计平均聚合。
- 掌握度可追溯：每道题有记录，掌握度 = 累计平均正确率（可解释）。
- 掌握表 key 从源头归一（canonical），「一元二次方程/解一元二次方程」不裂行。
- 掌握度页列式化数据支撑：题型 / 来源 / 掌握% / 训练数 / 跳转题目。

**Non-Goals（本期明确不做）：**
- 题型↔知识点关联、知识点总览覆盖度着色（前端断联，`kp-coverage` 接口保留但不消费）。
- **相似题存储/检索**：题目向量本期不落库（用户拍板「后续存在做打算」）；本期向量库只存「canonical 题型名 → 向量」，用于题型名归一。
- 题库建设（`t_question` 题库域已有，与「学生作答记录」是两回事）。
- 全局题型库（跨学生沉淀 canonical）——本期归一是 per 全局的题型名，掌握度仍 per 学生。
- **只记录「题目→题型」**：本期不新增「题型→知识点」数据写入；`t_kp_derived_obs`/`t_kp_question_type`/`t_kp_question_type_alias` 保留不动、独立演进。
- **题型↔知识点自动关联不做**：入口不自动关联知识点——查表只读 + 独立维护（见 Decision 10）；obs 共现自动聚合/挂起/澄清批处理本期停用。
- **不做定时任务**：聚合/维护/批量聚集全部按钮手动触发（现有 `POST /aggregation/run` + 新增手动接口），不新增 `@Scheduled`。

## Decisions

### 1. 两张表：题目表（事实源）+ 掌握表（聚合结果）

```
t_student_question_record        t_student_topic_mastery（改造）
  id, student_id                   id, student_id
  content（题目文本）                topic_key（canonical，唯一）
  source（ai/bank）                 topic_label
  topic_label（原始/归一）           mastery（连续 0-100，累计平均）
  score（0.0/0.5/1.0 × 打折）       train_count
  hint_count, answer_request_count  source（ai/bank）
  session_id, created_at            updated_at
```

- **题目表是事实源**：每道题一条记录，含对错信号与引导轮数，可回查。
- **掌握表是聚合结果**：canonical key + 累计平均。两张表隔离「题目证据」与「聚合值」——后续改折扣系数/信号映射，重算聚合即可，题目证据不丢。
- **掌握表改造 vs 新表**：改造现有 `t_student_topic_mastery`（加 `source`/`train_count`，`mastery_level` 语义从「置信度」改「正确率累计」）。历史数据量小：保留旧值作初始正确率、`train_count=1`（平滑过渡，见 Migration）。

### 2. 掌握度 = 累计平均正确率（替代 max 单调不减）

```
new = old × n/(n+1) + score × 1/(n+1)     // n = train_count
train_count += 1
```

- **为什么累计平均**：正确率视角，可解释、稳定、不抖动。「某题型练 10 道对 6 道 = 64%」业务含义通透。
- **备选**：max 单调不减（现状，置信度视角，答错不降分）——与「可追溯正确率」诉求冲突；EWMA——比累计平均更「敏感近期」，但更难解释、难回查。
- **一次作答算一次**：不做题目去重，同一道题做两次计两次训练数（反映真实练习量）。
- **打折作用于 score 不作用于结果**（避免「第一题答错 → 题型 0%」的假低）。

### 3. 掌握信号映射：直接答对 / 引导后答对 / 答错，Python 零改动

```
直接答对（answer_request_count=0，学生未主动求助）→ score = 1.0
求助后答对（answer_request_count≥1，学生要过思路/答案）→ score = 0.5
答错 / 未完成                                   → score = 0.0
× per-题型前几题打折（第1题70% / 第2题80% / 第3题起100%，可配置）
```

- **复用现有资产**：会话实体已有 `roundCount`（引导轮数）、`answerRequestCount`（要答案次数），Java 侧直接取，**Python 不新增字段**。
- **为什么用引导量而非 hinted 布尔**：连续引导量（hint_count/answer_request_count）比布尔更细，将来可 `0.6^hint_count` 衰减；且不触 Python 契约。
- **打分 scoping = per 题型**（对每个题型，它的第 1 题打折）——学习新题型都是从不会开始；与现状 per-题型 max 天然一致。

### 4. 题型聚集 = 动态涌现（零锚点，核心）

**场景**：无题库、无预置分类。学生题目一条条来（AI 答疑），LLM 每次猜题型名（**弱标注**，会飘：鸡兔同笼/假设法/笼中鸡兔），没有预先定义的 canonical 池。

```
第 1 条题：向量桶无近邻 → 建 canonical（锚点诞生）
第 N 条题：题型名向量查最近邻 → 命中归并 / 未命中建新
批量（手动）：散名全量聚类 → 补归并 + LLM 归纳规范名 → 重算聚合
```

- **锚点是动态涌现的，不是预置的**：canonical 由「第一条相似题」创建（首见名/最高频名作 canonical 名），后续题目落进已有 canonical。池 = 向量桶里已聚集的题目，**从零长出来**。无题库也能跑通。
- **聚集依据 = 字符规则 + 题型名向量最近邻（单信号）**：
  - 字符级规则先拦确定性高频变体（「解X/求X」），省 embedding 调用（覆盖「解一元二次方程」类）。**编辑距离 ≤1 近字归并已移除**（联调拍板）——「一元一次方程/一元二次方程」一字之差与错别字「方成/方程」同为距离 1，字符级无法区分会误并；近字/错别字归并全交给题型名向量层（语义最近邻正确区分「一次/二次」、归并「方成/方程」）。
  - 题型名向量处理**语义同型**（鸡兔同笼/鸡兔同笼问题/假设法；「相遇 vs 行程」是否合并由阈值定）。
  - **题目向量本期不落库**（Python 契约「本期只传题型名」，对齐 Non-Goals）——聚集不依赖题面相似；题目文本仍落 MySQL 题目表作事实源，只是不参与向量聚集。相似题功能后续启用 `question` 索引。
  - 命中 ≥ 高阈值 → 直接归并；中阈值区间 → 进候选 LLM 仲裁；未命中 → 建新。
- **为什么向量而非纯 LLM 池约束**：池约束（`KpConstrainedAssociator`，已交付未接线）= LLM 从显式列表选最近；向量最近邻 = **同一逻辑的隐式向量空间版，且不需要预置池**（动态最近邻）。向量不依赖 LLM 调用（快/便宜/确定性强）、不受池 size 限制、天然处理语义变体。
- **掌握表 key = canonical（落库时动态锚定）**：所有题型名入口（`decide` label、`analyze-question` 结果）落库时查最近邻归并后落表。**锚定在落库前发生**，掌握表从源头不裂行——落库后合并（聚合 merge）不回流掌握表，治标不治本。
- **向量库存内容**：本期只存**题型名向量**（`vector_type="topic"` 路由到题型名索引；metadata：student_id / topic_label / canonical_label / timestamp）。题目向量不落库（相似题功能预留 `question` 索引，后续启用）。**相似题展示不做**（用户拍板「后续存在做打算」），向量只作聚集依据。**存储实现：Python 侧 COS Vector Bucket（见 Decision 5），Java 经桥调用，不碰 SDK。**

### 5. 向量存储 = Python 桥（COS Vector Bucket，无 Java SDK 方案）

**前提**：COS 向量检索只有 Python/Go SDK（`CosVectorsClient`/`VectorService`），**无 Java SDK**——排除「Java 直调 SDK」。

- **架构**：向量操作全在 Python 侧（复用已有 Java↔Python 桥模式，如 `TutoringLlmPort`）：
  - Python 提供向量端点：`POST /api/tutoring/vector/put`（题型名+metadata → dashscope embedding → `CosVectorsClient.put_vectors`）、`POST /api/tutoring/vector/query`（题型名+top_k → embedding → `query_vectors` → 返回 hits）。**query 响应字段名 `vectors`（非 `hits`）**——对齐 COS `query_vectors` 返回结构，Python 已实现（ai-edu-ai-service b7159c5）；Java 桥解析 `{"vectors":[{key,metadata,distance}]}`
  - **`vector_type` 必填路由键（Python 契约已定稿）**：每次 put/query 后端显式声明写/查哪个索引，**无缺省、无跨索引查询**；本期唯一合法值 `"topic"`（题型名向量索引）。未知 `vector_type` → Python 400 → **Java 降级**（回退字符规则 + 原样落库，正常失败路径）。后端不感知 COS 索引名——Python 内部 `COS_VECTORS_INDEXES` 路由表（本期 1 条，`question`/`rag` 为纯配置占位，后续加索引零代码改动）。
  - **embedding 在 Python 侧**（复用 gateway 的 dashscope 配置，text-embedding-v3，768 维）
  - Java 通过 `TopicVectorStore` 端口 HTTP 调 Python，**不碰 embedding API / COS SDK**
- **为什么 Python 桥而非自研**：① 用上已开通的 Vector Bucket（数据量上来能力强）② embedding 复用 Python 现有 dashscope 配置（密钥不散到 Java）③ **后续 RAG 复用同一套向量基础设施**（用户拍板：业务后续要做 RAG，需打通）
- **备选**：MySQL 自研（全 Java 零依赖，但不用 Vector Bucket、后续 RAG 要另起）；Java 直调 REST（自实现 COS 签名，成本高）
- **注意**：COS 是对象存储，**Vector Bucket 是独立的向量存储桶类型**，不是「对象存储 + 向量插件」。
- **写入异步生效（spike 实测，Java 桥必须知道）**：`put_vectors` 后索引 **~10s 异步**构建，**立即 `query` 会 miss**（空 `vectors`）——首题建锚后**无需立查**（本来无近邻）；聚集编排「put 后查」路径要容忍延迟/留重试；联调预期：建锚 put 后 ≥10s，后续题目 query 才可见近邻。
- **Python 侧改动范围**：仅**新增**向量服务端点（`vector_type` 路由 + embedding + put/query；decide/信号链路仍零改动）。**已交付**（ai-edu-ai-service b7159c5，241 测试绿）。

### 6. embedding 模型 + 阈值：dashscope 优先，spike 已实测（distance 契约，后端收口）

- **模型**：dashscope text-embedding-v3（768 维，中文 50+ 语种，OpenAI 兼容）——Python gateway 已接 dashscope，**成本已确认**（免费 50 万 token + 0.5 元/百万 token，10 块钱够用很久）。**已交付**：独立封装在 `vector_store.py`（未动 gateway factory），复用 `DASHSCOPE_API_KEY`。
- **备选**：ark doubao-embedding（火山，Python gateway 也接）；本地开源模型（text2vec/m3e，需 Python 部署）。
- **spike 实测（Python 端交付，2026-08-18）**：cosine **distance（越小越相似，非相似度）**——self ≈ 0、同型 ~0.077（鸡兔同笼→鸡兔同笼问题）、异型 ≥0.33（相遇→行程 0.332、鸡兔同笼 vs 异型 0.481）。同型/异型在 **~0.08~0.33 有清晰间距**。
- **阈值 = 归并旋钮（distance ≤ X 归并，代码按 distance 判定）**：保守默认 **0.2**（只并同型，不并异型；宁可拆不误并）、激进 **0.25**（逼近 0.33 异型下限）。「相遇 vs 行程」（0.332）不被 0.2 归并——**默认拆分**。后端收口后入 `application.yml`。

### 7. `getMastery` 契约变更（BREAKING，前端联调）

```
GET /students/{id}/mastery
响应 items[]:
  topicKey / topicLabel
  masteryLevel：0-100 连续百分比（原 0/25/50/75 离散四档）  ← BREAKING
  source：'ai' | 'bank'
  trainCount
  status：RESOLVED / PENDING（保留 PENDING=obs 有但未确认）
```

- **前端分桶保留四档视觉**（<25 待巩固 / 25-50 练习中 / 50-75 偏稳 / ≥75 已掌握）。
- **向后兼容**：加新字段而非删旧字段；`masteryLevel` 语义变更用版本或文档标 BREAKING。
- **`kp-coverage` 派生仍可工作**：知识点覆盖度 = clamp(Σ(题型掌握度×ratio), 0, 75)——连续正确率输入，派生逻辑不变（仅前端不再消费）。

### 8. 掌握信号跟题目走，不跟题型走

- 题型名未识别（PENDING）的题**照常采集信号**，落题目表；题型归属确定（归一/后续人工）后再聚合进掌握表。
- **为什么**：PENDING 是「题型暂时没认出」，不代表「题没做」——答对/答错信号是确定的，不能因题型待定就丢。

### 9. 两域解耦 + 手动触发（面试项目不做定时）

**本期只记录「题目→题型」**，与「题型→知识点」完全解耦：

```
域 A「题目→题型」（本期，掌握度）          域 B「题型→知识点」（保留不动）
  题目落库 → 向量聚集 → 掌握表累计平均        obs / 题型库 / 别名表 独立存在
  只消费题目记录，不依赖域 B                 不消费掌握度链路
  ↑ 一个环节故障不影响另一个，反之亦然
```

- **去定时**：移除 `KpBatchScheduler` 的 `@Scheduled`（aggregate 3:17 / maintain 3:37），聚合/维护改**按钮手动触发**——现有 `POST /api/kp/aggregation/run`（ADMIN）已具备；批量聚集新增手动接口（ADMIN 按钮）。
- **为什么手动**：面试项目不引入定时任务复杂度；聚合按需即时触发（联调/演示手动跑即可），掌握度链路不受聚合节奏影响。
- **canonical 共享**：两域共享 canonical 名（都是「鸡兔同笼」），经别名表作为收敛接缝——域 A 的向量归并写别名表，域 B 的 analyze 命中自动受益，但**不互相阻塞**。
- **analyze 返回 canonical（前端契约）**：`analyze-question` 返回的 `topicLabel` 必须过聚集 post-process（返回 canonical）——前端用它查 `getMastery`，若返回原始名（「解一元二次方程」）会 miss 掌握表（key=「一元二次方程」）→ 误判「未开始」。**前端联调契约**：
  - `analyze.topicLabel` = canonical（查得到掌握度）
  - `getMastery` PENDING 项 = 题目记录有但 canonical 未归属（域 B 独立化后不再来自 obs）；未开始 = 不在 `items[]`；masteryLevel 分桶 = 掌握表累计平均
  - 题目列表 `score` 与掌握表聚合同源（落库生效分值，可追溯「为什么 64%」）

### 10. 域 B 独立化：题型↔知识点 = 查表只读 + 独立维护（去自动关联）

**目标**：所有入口只到「题型」阶段；题型↔知识点关联由**独立逻辑**维护，入口只读。业务不成熟期不做自动关联。

- **入口流程（analyze-question / 答疑 decide）**：识别题型名 → 查题型库（`findByTopicLabelOrAlias` → `t_kp_question_type_kp` 分布桶）→ **命中返回权威分布 / 未命中返回「仅题型 + canonical + 空知识点」**——不挂起、不写 obs、不顺带 LLM kps。
- **独立逻辑 = ADMIN 维护接口**：题型 CRUD + 题型↔知识点分布绑定（`t_kp_question_type` / `t_kp_question_type_kp` / 别名表）——演示手动配几条数据，入口查表即命中；是下期「题型库管理后台」的雏形。**替代「obs 共现 → LLM 归纳 ratio」的自动涌现**。
- **停用自动涌现链路**：Python `understandQuestion` 顺带 kps 的消费、`upsertPendingIfAbsent` 挂起、学生 vote 澄清、聚合 `aggregate`（obs 共现自动关联）、`KpCoverageAppService` 派生（前端已不消费）。
- **PENDING 语义更新（承接 Decision 9）**：域 B 独立化后 analyze/decide 不再产生「题型→知识点」挂起 obs → `getMastery` 的 `status=PENDING` **不再来自 obs**，改为「题目记录有但 canonical 未归属」（题目表 `canonical_label` 为空，待聚集/待归属）。
- **为什么**：演示项目 + 题型↔知识点业务不成熟——自动关联引入 obs 状态机/聚合批处理/LLM 归纳 5 个环节，分散本期核心（题目→题型→掌握度）；手动维护一张表、入口查表，可演示、可解释、可控。

## Risks / Trade-offs

- [embedding 对数学术语区分度不足] → spike 前置：候选模型对比真实题型名，区分度不达标换模型（混元优先）。
- [阈值误合并/漏合并] → 阈值 = 粒度旋钮，spike 标定；误合并只影响个别题权重（累计百分比可容忍），漏合并后续人工/别名表补。
- [向量库冷启动（无近邻建新）] → 数据量上来归一越来越准；冷启动用字符规则兜底 + 建新 canonical。
- [历史掌握度语义迁移（置信度 → 正确率）] → 数据量小，旧值作初始正确率 + `train_count=1` 平滑过渡；掌握表加列非删列，回滚无损。
- [题目文本提取（零题目状态）] → 复用 `isNewQuestion` 换题检测（已有）挂落库触发器；题目文本取该轮题目，非「最后一条用户消息」。
- [`getMastery` BREAKING] → 加新字段不删旧；前端分桶保留四档视觉；`kp-coverage` 派生不变。
- [Python 端 decide 信号粒度] → 本期 Java 从 `roundCount`/`answerRequestCount` 推断，decide/信号链路 Python 零改动；若将来要更细信号再谈契约。
- [Python 向量端点不可用] → Java 桥失败回退字符规则 + 原样落库（不阻塞）；向量是增强层，主干（题目落库/掌握表/接口）不依赖向量。

## Migration Plan

1. **spike**（前置）：embedding 模型选型 + 阈值标定（50~100 真实题型名）。
2. **表结构**：新建 `t_student_question_record`；`t_student_topic_mastery` 加 `source`/`train_count`（`mastery_level` 语义改累计平均）。
3. **向量初始化（Python 侧）**：CosVectorsClient 建索引（768 维 cosine）+ **可选**种子（有知识点池/题型库时预置 embedding 加速收敛）；无则**从零动态积累**（首题建锚，不阻塞）。
4. **落库链路**：AI 答疑/题型分析入口接题目落库 + 聚集 post-process（动态锚定 canonical）。
5. **聚合改写**：`applyMasteryAndErrors` → 题目落库 + 累计平均；`getStudentMastery` → 连续百分比。
6. **接口**：按题型查题目列表；`getMastery` 契约变更（前端联调）。
7. **回滚**：掌握表加列非删列；`getMastery` 旧字段保留；向量库不接主链路（聚集失败回退字符规则 + 原样落库，不阻塞）。

## Open Questions

- ✅ **Python 向量链路（spike）**：已交付（ai-edu-ai-service b7159c5）——CosVectorsClient 建索引（768 维 cosine）/ put/query 跑通、权限已授权、近邻实测数据见 python-integration 第六节。
- ✅ **embedding 模型 + 阈值**：已定——text-embedding-v3（768），distance 归并阈值默认 **0.2（保守）**，见 Decision 6。
- ✅ **聚集粒度**：已定——「相遇(0.332)/行程」默认拆分（0.2 阈值不归并），宁可拆不误并。
- **canonical 命名**：本期采用「首见名/最高频名兜底 + 定时 LLM 归纳规范名」（Decision 4）；命名策略可调。
- **原题链接**：题目表 `session_id` 跳回答疑会话（已有字段），掌握度页「查看题目」展示会话链接；无会话链接显示题目原文。
- **掌握表改造 vs 新表**：本期倾向改造现有表 + 平滑迁移；若历史数据迁移有风险可退化为新表并行。
