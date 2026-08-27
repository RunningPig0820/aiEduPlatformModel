# kp-question-analysis-backend 技术设计

## Context

- **现有能力**：`POST /api/kp/resolve`（题型名 label → TextbookKP URI，管线 ①镜像 → ②题型库年级匹配 → ③LLM 消歧 → ④PENDING，写 obs）、`POST /api/kp/vote`（学生确认落 STUDENT_VOTE 观测）、题型库聚合任务（凌晨扫 obs 建 CANDIDATE + LLM 归纳 ratio）、题型库分页 + 关联知识点接口。全部已收口（`kp-matching-lightup`）。
- **缺口**：`resolve` 是 **label 级**，需先知道题型名；「题目文本 → 题型名」的题目理解只在答疑 Python `decide` 会话内（SSE 绑定），无独立 REST。
- **题型库健康问题**：聚合按 `topic_label` **逐字聚类**（`groupingBy(getTopicLabel)`），相似题型叫法不一（「鸡兔同笼」vs「鸡兔同笼问题」）裂成重复条目、聚合阈值（≥3 学生/≥5 命中）被劈开稀释；学生确认 vote 的 topicLabel 也会落成重复题型。
- **前提**：无现成完整知识点/题库标注表；知识点用 TextbookKP URI 锚定（kg-sync 镜像），题型名 ≠ 知识点名，靠 LLM 翻译 + 镜像校验 + 观测共现桥接（kp-matching-lightup design Decision 21 两段式消歧）。

**已拍板（用户）**：题目理解 Java 自研（端口预留，可后续换 Python 独立端点）；本期范围 = 核心两件（analyze-question 端点 + 题型库别名合并），Q3 跨来源观测、Q4 批量扫题库为后续阶段。

## Goals / Non-Goals

**Goals:**
- `POST /api/kp/analyze-question { text }`：题目文本 → 识别题型名 → 返回关联知识点清单；**纯分析不写 obs**；PENDING 不报错、携带澄清候选。
- 题型库别名合并：相似题型名收敛到 canonical 题型 + 同一 kp 分布；`resolve`②/`vote`/聚合均按别名命中，聚合阈值不再被变体稀释。
- 题目理解端口抽象（domain），Java LLM 为默认实现，Python 独立端点可替换。

**Non-Goals:**
- 管理端/老师端全局审核（`kp-pending-review`）——本期学生确认只走个人观测。
- 题库域已有题型标签当种子观测（Q3 跨来源）——后续阶段，本期不为题库域类型建模。
- proactive 批量扫题库自动补题型（Q4）——后续阶段。
- Python 独立题目理解端点——本期只留端口，不跨仓库。
- 掌握度层变体合并（`t_student_topic_mastery` 的 topic_key 分裂）——kp-matching-lightup Decision 17 归一化已折叠硬变体（全角/空白/末尾标点），语义级同义词聚类留大数据阶段。

## Decisions

### D1. 题目理解端口抽象，Java LLM 默认实现（题型名 → 空挂库锚）

新增 domain 端口 `QuestionUnderstandingPort`：

```java
/** 题目文本 → 候选题型名（LLM 题目理解）。纯识别，不查库不落库。 */
List<String> understand(String questionText, Integer grade);
```

默认实现 `KpQuestionAnalyzer`（infra，`@Component`）：复用 `LlmGateway.chat()` + 新 prompt「识别这道数学题的题型名，每行一个，限 1~5 个，不要编号/解释」，解析复用 `KpLlmDisambiguator.parseNames` 的去编号/bullet 逻辑。

**关键：prompt 注入题型库已收词**——把当前题型库 top-N 常用题型名（`QuestionTypeRepository.findTopTopicLabels(20)`）作为「参考题型词表」带进 prompt（"优先从参考词表选取，词汇不足可自拟"）。让 LLM 的题型命名**偏向现有词汇**，从源头降低变体漂移（这是别名合并之外的第一道防线，纯 prompt 零成本）。LLM 失败 → 返回空列表，analyze-question 降级 PENDING。

**为什么 Java 而非 Python**（用户已拍板）：自包含、不阻塞跨仓库；词汇分歧由 D3 别名合并 + prompt 词表兜底。端口抽象保留 Python 独立端点（拆 decide 题目理解）为后续可替换实现——换实现只动 infra 装配，不动 domain/application。

### D2. analyze-question 纯分析，不写 obs（浏览不产生学习信号）

`TutoringKpResolverImpl.doResolve` 抽出 `persistObs` 开关：`resolve(label, studentId)` 保持写 obs（答疑语义），analyze-question 走 `persistObs=false` 的只读解析（镜像/题型库权威命中不落 obs，浏览噪声不污染聚合）。

**唯一例外（信任简化，见 D8）**：analyze 池约束选择的 **top-1 直接落 RESOLVED obs**（「最可能」信号进数据喂聚合，题型库冷启动也能沉淀）；学生确认 = 正确（vote 覆盖 top-1 纠正）。仅极端兜底（池空）才落 PENDING obs（`upsertPendingIfAbsent` 去重）挂起待补充。

### D3. 题型库别名合并：kp 分布重叠 → canonical + 别名表

新表 `t_kp_question_type_alias`（learning 库，V16 迁移）：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | 自增 |
| alias_label | VARCHAR UNIQUE | 变体题型名（已归一化） |
| question_type_id | BIGINT FK | canonical 题型 |
| created_at | DATETIME | 审计 |

聚合 `aggregateTopic` 建新 CANDIDATE 前改为：

```
① findByTopicLabelOrAlias(label)  命中 → 更新现有条目（现状，别名命中同样走到这）
② 未命中 → 与现有 CANDIDATE/STABLE 题型比 kp_uri 集合重叠：
      | 重叠 ≥ 70%（可配置）→ 视同变体：插入 alias + 本桶观测折叠进该条目
      |    kp 分布（upsert QuestionTypeKp 统计合并）+ updateStats
      | 无相似 → 新建 CANDIDATE（现状）
```

查询统一改 `findByTopicLabel(label)` → `findByTopicLabelOrAlias(label)`，覆盖：解析管线② `resolveByCatalog`、`recordStudentVote`、analyze-question、聚合步骤①。实现 = 一条 LEFT JOIN（alias→question_type）或先查 canonical 再查 alias 兜底。

**为什么按 kp 分布重叠而非归一化/字符串相似**：变体题型的**语义锚是它指向的知识点**（同一批 obs 的 kp_uri），重叠是确定性信号、零 LLM、零误判成本（两个不同题型共享一个知识点不会触发 70% 重叠）。字符串/归一化兜不住「鸡兔同笼」vs「鸡兔同笼问题」，kp 重叠天然兜住。LLM 级同义词（「牛吃草」vs「牛顿问题」无 kp 重叠但语义相近）留大数据阶段（kp-matching-lightup Decision 17）。

### D4. 解析管线②/聚合/vote 的查询统一走别名

`QuestionTypeRepository` 增 `findByTopicLabelOrAlias(String)`、`findTopTopicLabels(int)`（D1 词表用）。别名命中与 canonical 命中等价返回 `QuestionType`，调用方无感知。**canonical 名只增不改**（合并只加别名、不改主题名，避免破坏既有引用）。

### D5. analyze-question 接口契约

`POST /api/kp/analyze-question { text }` → `ApiResponse<QuestionAnalysisDTO>`：

```json
{
  "topicLabel": "鸡兔同笼问题",
  "status": "RESOLVED",          // RESOLVED / PENDING
  "confidence": 85,               // 0-100，PENDING 为 0
  "knowledgePoints": [
    { "kpUri": "…textbook…", "kpLabel": "鸡兔同笼", "gradeRange": "4-6", "ratio": 0.8 }
  ],
  "candidates": []                // PENDING 时填充，RESOLVED 为空
}
```

编排（`KpQuestionAnalysisAppService.analyze(text, studentId)`，确定性靠功能 + 提示词，**不依赖缓存**）：

```
① understand(text, grade) → 候选题型名 [t1, t2, …]（空 → PENDING 无候选）
② 遍历全部候选：任一 findByTopicLabelOrAlias(ti) 命中 → status=RESOLVED，
     knowledgePoints=该题型全部关联分布（数据驱动权威，结果与候选顺序无关）
③ 前 LLM_RESOLVE_BUDGET=2 个候选走 resolveReadOnly（镜像权威）：
     首个 RESOLVED 且非 WEAK → 单点 RESOLVED（短路）
     WEAK/PENDING → 收集候选（WEAK 的 kpLabel + PENDING candidates，镜像校验后）
④ 全无权威命中 → PENDING + candidates（candidates 已镜像校验，保证 vote 不 10003）
     + 落 PENDING obs「挂起来」（upsertPendingIfAbsent）
```

**行为要点（联调后定稿）**：
- **WEAK 降级**：冷启动 LLM 猜测返回 `PENDING`（KpResolution 加 `weak` 标记，不再冒充权威 RESOLVED），只作候选待确认。
- **candidates 镜像校验**：analyze 返回前经 `inMirror`（精确→LIKE）校验，非镜像 label 丢弃 → vote 不报 10003。
- **LLM 预算**：题型库全量遍历（DB 廉价），`resolveReadOnly`（含 LLM 消歧）只给前 2 个候选 → 冷启动最坏 1 次理解 + 2 次消歧 ≈ 3 次 LLM（原最坏 6 次）。
- **确定性**：同文本 status 稳定（无数据锚恒 PENDING）；candidates 冷启动下可能波动（LLM 非确定，数据锚积累后收敛）。`AiEduChatRequest` 无 temperature，不调参。

复用：`recordStudentVote`（确认）、`ocr`（拍题）、题型库分页/关联接口（浏览）。新增：`KpQuestionAnalysisAppService`、`KpResolutionController` 加 `POST /analyze-question`。

### D6. 越权与安全

`analyze-question` 用 `TutoringAuth.requireStudent(session)`（未登录 → 10004，非 STUDENT → 20004），与 api.md「需要登录（STUDENT）」契约一致。取不到年级时降级纯 LLM 题目理解（无年级锚，resolve 已有降级）。无管理功能暴露。`findTopTopicLabels` 只读不越权。

### D7. 存疑挂起闭环 + 联调修复（2026-08-17 联调后定稿）

产品闭环「存疑挂起来 → 学生选择/后续任务补充」三环全通：

```
analyze 存疑 PENDING
  ├─ 落 PENDING obs（upsertPendingIfAbsent 去重）「挂起来」→ 进 pending-kps，不丢
  ├─ 学生选择 → vote → resolvePendingByStudentTopic 转正该生该题型 PENDING → RESOLVED → 聚合沉淀
  └─ 学生不选 → 维护任务 rejudgePending：LLM 重判 → 高置信转 WEAK → 共现(≥2生)转正 → 聚合沉淀
```

**联调 4 bug 修复**：
1. **非确定性** → 全候选遍历（顺序无关）+ prompt 收敛（参考词表强制优先/按把握排序/「无法识别」兜底）+ 数据锚优先；**移除缓存**（提示词 + 功能点而非缓存，用户拍板）。
2. **关联错误（对数方程求解）** → ① 聚合 `findResolved`/`findResolvedByTopicLabels` **排除 WEAK**（LLM 幻觉不进题型库，WEAK 需第二信号转正才入）；② `KpResolution.weak` 标记 → analyze 对 WEAK 降级为候选待确认。
3. **candidates 恒空/时有时无** → 遍历兜底 + WEAK 的 kpLabel 也进候选 + 镜像校验（D5）。
4. **vote 未体现** → `resolvePendingByStudentTopic` 转正 PENDING（待确认清单即时消失）；无 PENDING 才新建。

新增仓储方法：`upsertPendingIfAbsent`、`resolvePendingByStudentTopic`、`resolveWeakByMaintenance`（均 learning 库 SQL）。

### D8. 封闭域约束选择：题目 → 学段知识点池 → LLM 从池选（恒非空）【2026-08-17 第二轮】【本期未接线】

> **2026-08-17 降级**：本期 analyze **不接池约束选择**（前端范围降级：题库 miss → PENDING，空可接受；题库↔知识点关联转「题库和知识点」独立迭代）。池约束编排已抽到 `KpPoolAssociateService`（组件 `KpConstrainedAssociator`/`findLabelsByStage`/粗筛/`keyword` 已交付、有测试），迭代启动时在 analyze ② 处接线即用。

**核心转变**：从「开放域自由猜测」→「封闭域约束选择」。当前 analyze 是 LLM 凭空猜题型→猜知识点（两段传递误差 + 猜不中返回空 = 流程死穴）。改为：题目 + 学生学段知识点 label 池 → LLM **只能从池里选**最相关 1-3 个 → 恒返回 top-N（置信低也返回池内最相近，**绝不空**）。

```
① 学段学科：resolveStudentGrade(studentId) → grade → stage；学科固定数学（当前仅数学，subject 预留）
② 题型库命中优先：题型识别命中 canonical/别名 → 权威分布（数据驱动，最快，D5 ① 保留）
③ 题型库 miss → 取学段知识点池 pool（该学段全部数学教材知识点 label，D9）
④ 粗筛子池：题目关键词 / 题型名 name-LIKE 召回（pool 可能 >LLM 上下文，先缩子池）
   - 子池空 → 回退全池截断（前 MAX=200，按章节顺序）
⑤ LLM 约束选择（KpConstrainedAssociator）：只能从子池选 1-3 最相关
   - prompt 强制「必须从池里选，不允许输出池外内容，不允许说无法确定」
   - LLM 失败 → 回退子池前 N 个（确定性兜底）
⑥ 结果恒非空：top-N 全为池内 label（天然镜像可 vote）；高置信 top1 → RESOLVED，否则 PENDING + candidates
```

**收益**：① **恒非空**——LLM 从有限池选必然命中，消灭「空候选死穴」；② **年级锚定**——池按学段过滤，消灭「小学鸡兔同笼→高中对数方程」跨学段错误；③ **确定性**——池确定，同文本结果稳定；④ **数据锚**——池来自教材知识点（镜像），非 LLM 幻觉。

**信任模型（简化，2026-08-17 定）**：
```
池约束选择 → top-1（最可能）+ top-N（候选）
  ├─ top-1 直接落 RESOLVED obs（进数据 → 聚合 → 题型库沉淀）【不管置信多低，无确认也进】
  ├─ 学生确认 top-1 → 已是正确（无操作）
  └─ 学生选别的 → vote → 覆盖 top-1（学生确认 = 正确）→ 纠正 obs + 题型库
```
- **学生确认 = 正确**：vote 是最高权威，覆盖 top-1 关联。
- **无确认 → top-1 进数据**：信任 LLM 池选择 top-1 为「最可能」，让题型库冷启动也能沉淀（学生不参与也长）。
- **错误整理**：错误 top-1 由 vote 纠正 / 维护重判 / 管理端审核（P2）整理（D11 飞轮）。
- 不再依赖「WEAK 等第二信号」作为进库门槛（analyze 的 top-1 直接 RESOLVED）；WEAK 保留给答疑主流程 resolve 的 LLM 消歧（仍排除聚合防幻觉）。

**与现有组件关系**：`KpQuestionAnalyzer`（题型识别）降级为「① 题型库命中 + ④ 子池召回」的粗筛器之一，不再是唯一关联入口；`KpLlmDisambiguator`（开放域消歧）退为维护任务重判用（PENDING→WEAK），analyze 关联走 D8 约束选择。grade→stage 复用 `KpCoverageAppService.toStageCode`。

### D9. 知识点池获取 + keyword 搜索兜底

- `KgKnowledgePointRepository.findLabelsByStage(stage)`：按学段取知识点 label 池（D8 ③ 用，全量教材知识点）。
- `POST /api/kg/knowledge-points` 支持 `keyword` 参数：`WHERE label LIKE CONCAT('%', #{keyword}, '%')`（在 stage 过滤内）→ 前端 `KpSearchSelector` 空候选时手动搜教材知识点确认（选中 kpLabel 走 vote，镜像天然可 vote）。

### D13. 图片题目多模态直看（2026-08-17 Python 拍板方案 B）

图片题目默认走**多模态视觉模型直接看图**（不经 OCR，OCR 仅前端失败兜底）。Python 已拍板方案 B：新增 stateless 端点 `POST /api/tutoring/question-understand`，**模型 Python 侧写死**（TUTORING_DECIDE_MODEL = `doubao-seed-2-0-mini-260428`，Java 不指定模型，模型是 Java 黑盒；方舟开通 ID 若不同，改 Python `question_understand.py` 一行，Java 无感）。

```
Java POST /api/kp/analyze-question/image (multipart)
  → 无会话上传 COS（tutoring/questions/{studentId}/analyze/{ts}.ext，无 sessionId 依赖）
  → generatePresignedUrl（Python 要签名 URL，getUrl 非签名不可用）
  → 传 topicHint=findTopTopicLabels(20)（视觉识别命名朝题型库收敛）
  → 调 Python /api/tutoring/question-understand { image_url, topic_hint, grade }
  → 返回 { topic_labels, question_kps }
  → ①题型库命中权威 → ②questionKps 顺带展示（镜像校验，不强求）→ ③PENDING 挂起
```

- **为什么不经 `/api/llm/chat`（方案 A）**：不是所有模型都是视觉功能——通用 chat 路由到非视觉模型图就废了。方案 B 模型写死视觉 + 独立端点，非视觉风险天然隔离。
- **契约字段（snake_case，tutoring 域统一）**：请求 `image_url`/`topic_hint`/`grade`；响应 `topic_labels`/`question_kps`。Java `QuestionUnderstandRequest/Result` 已加 `@JsonProperty` 映射。
- **降级**：topic_labels 空 = 识别失败 → PENDING（与文本路径一致，不报错）。

### D12. 前端范围降级（2026-08-17 前端告知）

前端本期降级为「**贴题 → 识别题型（核心）+ 知识点顺带参考（有则展示，无则不强求）**」，知识点关联的确认/搜索/待确认闭环转后续独立功能「题型↔知识点关联完善」。

**后端零改动**：现有 analyze-question（含 D8 池约束恒非空）是严格超集，满足降级后范围；D8 池约束选择 / D9 keyword 搜索 / 聚合手动触发已实现，供后续独立功能直接复用，非本期待办。掌握度主体=题型、知识点覆盖度派生（不与本题型知识点直接耦合）与前端「掌握度=掌握的题型」定位一致。

### D11. 设计原则：逻辑优先于数据准确，数据可后整理（2026-08-17 定）

**原则**：先打通「题目 → 关联 → 确认 → 沉淀」逻辑闭环，**不因数据残缺/不准阻塞实现**。恒非空返回「池内最相近」允许出错——错误由后续机制整理，而非阻止流程。镜像/题型库残缺是冷启动常态，飞轮转起来后自然收敛。

**各类数据错误 → 对应整理机制（设计已预留）**：

| 数据错误 | 整理机制 |
|---|---|
| **top-1 猜测不准**（信任模型：直接进数据） | **学生 vote 纠正**（确认=正确，覆盖 top-1）+ 维护重判整理 |
| LLM 幻觉关联（答疑 resolve 消歧，如「对数方程求解」） | **WEAK 排除聚合**（不固化进题型库）+ 维护重判 |
| 历史错误 obs | **维护任务 LLM 重判** → WEAK/READJUDICATED/HUMAN_REVIEW |
| 相似题型重复条目 | **别名合并**（kp 重叠 → canonical 收敛） |
| 最终残留错误 | **管理端审核**（P2，人工校准喂题型库） |
| 存疑数据（极端池空） | **挂起**（PENDING obs）不删，待学生/任务/人工整理 |

**可完成性判断**：代码层「打通闭环」（组 10 P0）无技术阻碍、一天内可完成；质量收敛依赖真实数据飞轮（学生确认参与），是产品积累曲线而非代码交付。镜像数据量可后查（信息化非阻塞）。

### D10. P1/P2 增强（非本次必须）

- **聚合手动触发**：`POST /api/kp/aggregation/run`（ADMIN）→ `aggregationService.aggregate()`。联调时即时验证题型库沉淀（现状凌晨 3:17 定时，看不到效果）。
- **管理端审核页面**（P2，独立功能点，后续）：学生题型 ↔ 年级知识点对照，LLM 批量分析关联 + 人工校准 → 喂题型库（`kp-pending-review`）。

## Risks / Trade-offs

- [LLM 题目理解幻觉题型名] → 下一步 resolve 兜底（PENDING 不报错）+ 学生确认；题型库命中才算可靠；prompt 注入词表收敛命名。
- [kp 重叠阈值误并（两个真实不同题型共享大量知识点）] → 阈值 70% 保守 + 可配置；合并只加别名、不动 canonical 名，误并可后续拆。
- [别名表增长（变体无限）] → 别名仅聚合命中时插入，且有 UNIQUE；聚合是离线低频任务；长期同义词收敛仍留大数据。
- [analyze 权威结果不写 obs → 冷启动题型库空] → 预期（浏览噪声不污染聚合）；存疑落 PENDING obs + vote/维护任务补充；题型库随答疑/投票/确认逐步积累，测试环境需真实数据或手动触发聚合。
- [candidates 冷启动波动] → status 稳定（无数据锚恒 PENDING），candidates 内容波动属 LLM 非确定；数据锚积累后收敛，前端容忍动态候选。
- [WEAK → PENDING 频率变高] → 冷启动猜测不再冒充 RESOLVED，PENDING 分支成常态路径；前端需覆盖「有 candidates」与「candidates 空」两种。
- [学段知识点池过大（数百）→ LLM 上下文超限] → 粗筛子池（题目关键词/题型名 name-LIKE）先缩容；子池空回退全池截断（MAX=200）；LLM 失败回退子池前 N 个（恒非空兜底）。
- [粗筛子池漏召回正确知识点] → 子池空/过小回退扩大召回（全池截断或去掉关键词过滤）；候选覆盖学段全池，仅排序由 LLM 决定。
- [掌握度层变体分裂未解] → 本期 Non-Goal；归一化已折叠硬变体，语义变体留大数据阶段。

## Migration Plan

1. V16 迁移：`t_kp_question_type_alias`（learning 库，含 UNIQUE(alias_label) + FK(question_type_id) + 索引）。**Flyway 关闭，需手动执行**（同 kp-matching-lightup 教训）。
2. domain：`QuestionUnderstandingPort`、`QuestionTypeAlias` 实体、仓储接口 `findByTopicLabelOrAlias`/`findTopTopicLabels`/别名 upsert。
3. infra：`KpQuestionAnalyzer`（LLM 实现）、别名 PO/Mapper/仓储实现（`@DS("learning")`）。
4. application：`KpQuestionAnalysisAppService`；`TutoringKpResolverImpl` 抽 `persistObs`；聚合 `aggregateTopic` 加别名合并。
5. interface：`KpResolutionController` 加 `POST /api/kp/analyze-question`。
6. 回滚：新增端点/表，无破坏性变更；回退关端点 + 删别名表即可，`resolve`/`vote`/题型库接口契约不变。

## Open Questions

- Python decide 后续是否拆独立题目理解端点（端口已预留，等 Python 侧有空，D1）。
- kp 重叠合并阈值（70%）是否需按科目/题型规模配置化微调——先固定常量，接大数据后再议。
