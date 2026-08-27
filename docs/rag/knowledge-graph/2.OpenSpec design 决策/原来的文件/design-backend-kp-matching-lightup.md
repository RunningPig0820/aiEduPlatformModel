# kp-matching-lightup 技术设计

## Context

- **现状**：AI 答疑的 decide 已能输出自由文本知识点标签（`question_kps` / `mastery_signals`），但 `TutoringKpResolverImpl` 只做「精确 → LIKE → 未命中丢弃」，真实题型（鸡兔同笼）大量落不到图谱，掌握度链路断裂。
- **权威图谱**：教育局下载，Neo4j 为主 + kg-sync 镜像 `t_kg_knowledge_point`（uri/label）。图谱节点带 URI，前端图谱页（`KnowledgeGraph.jsx`）能按 `node.id` 匹配。
- **掌握度**：`t_student_kp_mastery` 按 `kp_key`(URI) UPSERT，`GET /api/students/{id}/mastery` 已存在，但前端 `getStudentMastery` 定义了没人调用，且学生端没有图谱页（只有 admin 图谱页）。
- **关键约束**：权威图谱（Neo4j + kg-sync 镜像）**零写入**。题型空间无限、图谱节点有限，无限业务数据必须与有限权威结构分存。

## Goals / Non-Goals

**Goals:**
- 让 AI 题型可靠解析到教材知识点 URI（跨年级、可纠错、低置信挂起）。
- 从答疑数据沉淀"知识点的题型库"（个体派生 → 共现聚合 → 稳定），业务隔离。
- 掌握度主体翻转：题型直接观测落库（`t_student_topic_mastery`），知识点覆盖度运行时派生，学生端可见（绿/黄/红 + 疑似态）。
- 派生层全自动维护闭环（冲突检测 → 重判 → 回流先验），权威图零写入。

**Non-Goals:**
- **不写 Neo4j**；不做 embedding 语义聚类（后续大数据手段）。
- 不做消费方：变式题生成、错题本分组、薄弱点溯源（LangGraph 阶段 2 复用）。
- 不改变掌握度单调策略（保持"只升、显式纠正才降"）。
- 本期不做掌握度自动迁移（错解析回退只打标 + 人工复核，见 Decisions §6）。
- 本期不删除/迁移旧 KP 掌握度表 `t_student_kp_mastery`（并行过渡，见 Decisions §20）。

## 模块归属（DDD 域定位）

方案核心业务落在 **learning 域**；答疑入口与权威图谱边界如下：

| 组件 | 归属 | 说明 |
|------|------|------|
| 派生数据 3 表 + 掌握度 + 点亮 + 审核 | **learning 域** | 数据落 `ai_edu_learning`；掌握度本属 learning（knowledge mastery tracking） |
| 解析管线 `TutoringKpResolverImpl` | `infrastructure/ai/tutoring`（答疑 AI 集成层） | 跨域服务：消费答疑 label → 调用 learning 仓储 → 产物落 learning |
| 权威图谱 Neo4j + kg-sync 镜像 | **edukg 域（只读）** | 派生层只借 `kp_uri`，零写入 |

**learning 域 4 层落点**：

- domain：`com.ai.edu.domain.learning`（`DerivedKpObs` / `QuestionType` / `QuestionTypeKp` 实体 + 仓储接口）
- infrastructure：`com.ai.edu.infrastructure.persistence.learning`（MyBatis-Plus 实现 + Flyway）
- application：`com.ai.edu.application.service.learning`（聚合 / 维护服务）
- interface：`com.ai.edu.interfaces.api.learning`（resolve / pending / confirm / mastery 控制器）

> 注：`tutoring` 不是 domain 域，答疑 Java 网关在 `infrastructure/ai/tutoring`，属 AI 集成层而非业务域。

## Decisions

### 1. 派生层只存 MySQL，权威图谱只读

**决策**：题型派生层 3 张表全部放 `ai_edu_learning`，Neo4j 与 kg-sync 镜像只读。

**理由**：题型空间无限（鸡兔同笼、相遇、浓度…无穷），教材知识点有限（可数）。把无限挂到有限上会让图爆炸、污染权威结构。派生层以 `kp_uri` 为钩子"借"权威结构，图逻辑（兄弟/前置/关联）走现有 `KgNeo4jService` 只读展开。

**替代方案**：派生节点物化进 Neo4j 扩展命名空间（`ExtAlias` + `ALIAS_OF` 边）。**拒绝**：现阶段无图遍历需求（MySQL 键值够用），且增加权威图耦合；留待阶段 2 需图遍历时再评估。

### 2. 解析管线：年级锚 + 镜像 + 题型库先验 + LLM 消歧 + 挂起

**决策**：`TutoringKpResolverImpl` 重写为管线，命中顺序：

```
① kg 镜像精确 / LIKE（现有逻辑，0 成本）
② 题型库 grade-matched（STABLE/CANDIDATE 中按学生年级取占比最高 kp → 数据驱动先验）
③ LLM 消歧（topic + 镜像/题型库候选 label 列表 → LLM 选最匹配 + 置信度）
④ 低置信/歧义 → 学生澄清（可选，见 Decision 8 信任模型）→ 学生选则落 source=student_vote 观测
⑤ 学生跳过或仍歧义 → PENDING → 落 t_kp_derived_obs(status=PENDING) → 挂起，不点亮
```

**年级锚**：学生年级是"同一题型不同年级归不同 kp"的主信号（鸡兔同笼：四/五年级→假设法，七年级→二元一次方程组）。年级来自组织系统（学生→班级→年级），图谱 URI 内嵌年级（`renjiao-g1s`=一年级上）可距离排序。**年级是强先验非硬规则**：跨年级薄弱是 feature，LLM 上下文 + 置信度可覆盖。

**LLM 消歧接入**：复用现有 `llm-gateway`（或 Python 消歧端点），开放决策见 Open Questions。

**候选列表质量**：③ 冷启动消歧的候选生成见 Decision 21（LLM 生成候选名 + 镜像校验）；题型库已有先验时优先走②年级匹配，LLM 只兜底。最终 kp 必经镜像校验（SHALL NOT 凭空生成镜像不存在的 kp）。

### 3. 三张表数据模型

**`t_kp_derived_obs`（个体派生/观测，长期尾·无限）**

| 字段 | 说明 |
|---|---|
| `id` | 主键 |
| `student_id` | 学生 |
| `topic_label` | AI 题型/知识点原文（"鸡兔同笼"） |
| `kp_uri` | 解析结果（TextbookKP URI），可空（PENDING） |
| `student_grade` | 解析时学生年级（快照） |
| `confidence` | 解析置信度 0-100 |
| `source` | `llm`/`mirror`/`catalog`/`curated`/`student_vote` |
| `status` | `NEW`/`WEAK`/`RESOLVED`/`CONFLICTED`/`READJUDICATED`/`HUMAN_REVIEW` |
| `occurrence_count` | 同生+同题型+同URI 累计次数（去重，非重复行） |
| `first_seen_at` / `updated_at` | 时间线 |

> UNIQUE(`student_id`, `topic_label`, `kp_uri`)。同生再次遇到同题型 → count+1，不建新行。

**`t_kp_question_type`（聚合题型库主表，精选·有限）**

| 字段 | 说明 |
|---|---|
| `id` | 主键 |
| `topic_label` | 题型名（UNIQUE） |
| `status` | `CANDIDATE` / `STABLE` |
| `definition` | LLM/人工 补的定义（可空） |
| `hit_students` | 去重学生数 |
| `hit_count` | 总命中次数 |
| `promoted_by` | 首个触发学生（溯源） |
| `created_at` / `updated_at` | 时间线 |

**`t_kp_question_type_kp`（题型↔知识点 年级分布，1:N）**

| 字段 | 说明 |
|---|---|
| `id` | 主键 |
| `question_type_id` | → 题型主表 |
| `kp_uri` | 对应知识点 |
| `grade_range` | 该 kp 覆盖年级段（"4-6"） |
| `hit_students` / `hit_count` | 该分布桶统计 |
| `ratio` | 该 kp 占比（先验用） |

> 例：鸡兔同笼 → `假设法`(4-6, 38) + `二元一次方程组`(7-8, 21)。解析②就是查这张分布表按年级取占比最高。

> 备选：分布存 JSON 列简化表数；**选子表**——便于按 `kp_uri` 查询（消费方/错题/变式题都需要按知识点反向找题型）。

### 4. 聚合阈值（配置化）

| 阶段 | 条件 |
|---|---|
| 进 CANDIDATE | `(topic)` 去重学生数 ≥ 3 且 总命中 ≥ 5 |
| 升 STABLE | 审核通过 + 去重学生数 ≥ 10 且近 30 天仍增长 |

聚合桶按 `topic_label`（分布子表再按 kp 拆）。阈值进 `application.yml`（`ai-edu.kp.aggregation.*`）。

### 5. 自动维护闭环（保守）

周期任务（`@Scheduled`，如每日）：

```
错误信号 → 扫描 CONFLICTED/低置信/分布异常行
  → 用「年级锚 + 题型库先验 + LLM」重判
  → 变化时：更新 obs + 更新题型库统计（先验漂移）
  → 仍歧义 → status=HUMAN_REVIEW → 管理端「待确认」队列
```

**错误信号来源**（自动，无人盯）：
- decide 诊断冲突：LLM 说"卡在假设法"但 obs 记了二元一次方程组 → `CONFLICTED`。
- 掌握度矛盾：该生二元一次方程组已 mastered 却仍在鸡兔同笼上 struggling 且归到它。
- 年级分布异常：题型在某年级段分布出现非预期尖峰 → 触发重审。
- 低置信：confidence < 阈值 → 直接重判。

**保守原则**：只有高置信重判才自动改；LLM 也摇摆、无年级锚的进人工。一次修正回流先验 → 全体学生受益（"共享维护"）。

### 6. 点亮 + 疑似态

**决策**：掌握度显示 = 掌握值 × 置信档位两维。

| 档位（MasteryLevel 五档） | 掌握值 | 语义 | 前端视觉 |
|---|---|---|---|
| notStarted | 0 | 未开始（还没学） | ⚪ 中性灰 |
| beginner | 25 | 入门/薄弱 | 🔴 红 |
| intermediate | 50 | 进阶/练习中 | 🟡 黄 |
| advanced | 75 | 高级/掌握 | 🟢 绿 |
| master | 100 | 精通 | 🟢 深绿 |
| 解析低置信/挂起 | — | **疑似** | ⚪ 虚线 +「待确认」角标 |

- 挂起 label **不落掌握度**（不污染数据），前端渲染"疑似薄弱"待确认态。
- `MasteryItemDTO` 增加 `status`(RESOLVED/PENDING) + `confidence`；前端再叠加 obs 的 PENDING 列表渲染疑似节点。

**掌握度回退（错解析）**：重判把 二元一次方程组→假设法 后，错记在旧 kp 上的掌握度**打标 `MIGRATED` + 挂人工复核**，不自动删（自动删可能丢真实信号）。本期只打标 + 记录迁移日志，自动迁移列为后续。

### 7. 学生端图谱页

- 复用 `KnowledgeGraph.jsx` 组件，新增学生路由 + 页面（当前学生端无图谱页，仅 admin 有）。
- 取图：现有 `POST /api/auth/kg/knowledge-points/graph`（节点带 uri）。取掌握度：增强后 `GET /api/students/{id}/mastery`。
- 匹配：`mastery.kpKey == node.id` → 按档位着色。疑似节点从 obs PENDING 列表渲染虚线 + 角标。

### 8. 信任模型：LLM 主裁判 + 学生意图信号 + 人工边界仲裁

**决策**：派生层需要持续维护，但"谁是最终裁判"不能单一押注 LLM / 人工 / 学生任一方。三者各有不可替代的位置，按"各做其最擅长的事"分工：

| 角色 | 定位 | 职责 | 为什么能信 / 不能信 |
|---|---|---|---|
| **LLM** | 主裁判（默认引擎） | 日常解析 + 批量重判 | 可规模化、可复现、可交叉验证（多模型/温度）；错误"可治理"（换模型/接地/后验校验）。但会幻觉、有系统性偏见 |
| **学生** | 意图信号源 | 低置信时回答"你想学哪个" | 对自己的主观意图是唯一权威（问意图而非事实）。但会乱点/恶意，只当软信号 |
| **人工** | 边界仲裁 | 仅处理 LLM+学生都摇摆、或"高置信但矛盾"的极少数边界 | 要找懂学科的人；开发者已脱离真实解题，**不做日常打标** |

**理由**：信任度 = 准确率 × 可复现性 × 可规模化 × 可治理性。LLM 单次准确率不及领域专家，但错误有规律、可度量、可批量对冲；人工错误随机且不可规模化对冲；学生错误是恶意+随机的脏噪声。故 LLM 最适合做规模化主裁判。

**反作用力（关键）**：正因最信任 LLM，其每次判断 SHALL 能被客观信号校准（学生意图、做题结果、多模型交叉），否则滑回"LLM 用自身偏见确认自身偏见"的自证循环。

**学生澄清交互**：解析低置信/歧义时，不再静默 PENDING，而给学生可选澄清——"这道题你想学哪一块？A 假设法 / B 二元一次方程组 / C 跳过"。学生选 A/B 落 `t_kp_derived_obs(source=student_vote, confidence=中等)`，**只碰学科概念不碰 kp_uri**，跳过即弃权。防恶意：只影响自身观测、票数被多数稀释、≥3 人一致才进候选。

**票权重**（歧义时的优先级）：LLM 高置信（≥阈值）→ 直接 RESOLVED，学生票不覆盖；LLM 低置信/摇摆 → 问学生，学生票优先于 LLM 低置信（问的是主观意图，学生天然权威）；学生票 confidence 中等（默认 60），不视为 100 确定，仍需 ≥3 人去重一致才进候选。

### 9. 冷启动弱化：首条 LLM 消歧不直接点亮

**决策**：题型库无先验支撑时（冷启动首条），LLM 消歧结果 SHALL 标记 `status=WEAK`（弱确定），**不直接点亮**、不直接进题型库先验；满足任一"第二独立信号"才转 RESOLVED：

1. 同生后续做题结果佐证（用该知识点解对了同类题）；
2. 第二名不同学生对该题型消歧到同一 kp（共现佐证）；
3. 学生澄清投票达到阈值且方向一致。

**理由**：冷启动种子 100% 依赖 LLM，是最不可靠的一环。让"确定性"来自「重复 + 客观结果」而非 LLM 一句话，防止高置信幻觉直接结晶。

### 10. 客观结果后验 + 多模型交叉

**决策**：关联"对"的最终客观判据 = 它能否解释学生的做题结果。维护重判 SHALL 纳入该生做题结果（对/错 + 用哪个知识点解）：若 obs 归到假设法、该生却用二元一次方程组解对了同类题 → 关联可疑，触发 CONFLICTED 重判。做题结果是独立于 LLM 的客观信号，作为 LLM 重判的校准输入。

**多模型交叉**：冷启动消歧与维护重判 SHALL 支持多模型/多温度交叉（默认主模型 + 1 交叉模型投票），打断"同一偏见自证"；交叉结果不一致 → 置信度下调，走学生澄清或转人工。

### 11. 在线 vs 离线边界：大数据逻辑单独隔离

**决策**：派生层逻辑按「实时在线」与「离线批处理」拆分：

| 类型 | 逻辑 | 位置 |
|------|------|------|
| **在线（实时）** | 解析管线（写 obs + 读题型库先验）、掌握度点亮 | 业务域（learning / ai/tutoring） |
| **离线（批处理）** | obs→题型库聚合、维护重判、先验漂移 | `com.ai.edu.application.service.batch` |

离线逻辑单独拆到 `batch` 包，`package-info.java` + 类 javadoc 明确标注「逻辑归宿=大数据平台，当前后端 @Scheduled 过渡实现」。

**理由**：聚合/维护本质是离线批处理（不要求实时、obs 无限长尾），理想归宿是大数据平台；当前项目纯 Java DDD 后端未接大数据，故先以 @Scheduled 过渡。数据表（obs/题型库）为中性结构，大数据可直接读写，未来迁移只需替换 batch 包，在线解析管线②与数据表不变。

### 12. 学生端疑似接口 + obs 接入答疑主流程

**决策**：补两个前端对接暴露的缺口：

1. **学生端疑似接口** `GET /api/students/{id}/pending-kps`：返回该生 `status=PENDING/WEAK` 的派生观测（学生权限，studentId 必须等于会话 userId）。学生端"待确认清单"（疑似薄弱点）的数据源。
2. **obs 接入答疑主流程**：`applyMasteryAndErrors` 升级为调用 `resolve(label, session.getStudentId())`（替代 `resolveLabelToUri` 的 default 兼容路径），使解析产生 obs、年级锚生效；掌握度写入同步取 status/confidence（不再硬编码 RESOLVED）。

**理由**：前端对接暴露两个断层——(a) `getMastery` 硬编码 RESOLVED，学生拿不到自己的疑似点（现有 pending 接口是 ADMIN/TEACHER 专属且返回全体）；(b) 灰度遗留：`resolveLabelToUri` 传 null，obs 派生层未接进答疑主流程，题型库聚合/维护闭环无输入数据。

### 13. 知识点学段/章节归属反查（mastery stage 字段）

**决策**：`MasteryItemDTO` 增加 `stage`（primary/middle/high）+ 可选 `chapterLabel`/`sectionLabel`。反查链路沿用现有 `getKnowledgePointDetail` 的 kp→section→chapter 两级，再延伸一跳 chapter→textbook 取 stage：

```
kp_uri → t_kg_section_kp → t_kg_chapter_section → t_kg_textbook_chapter → t_kg_textbook(stage)
```

**批量反查**：新增值对象 `KgKpPlacement`（kpUri/stage/chapterLabel/sectionLabel）+ `KgKnowledgePointRepository.findPlacementByUris(List<String>)`，Mapper 一条 LEFT JOIN SQL 批量反查（`getStudentMastery` 一次返回多 kp，避免 N+1）。一个 kp 挂多个 section 时取首个非空 stage（跨教材同 kp 罕见，取先收录）。

**理由**：学生掌握点天然跨年级（三年级可问初中内容），"按年级框定范围"的前提不成立；学段是更宽更稳的分组粒度。`stage` 已在 `KgTextbook.stage`（与 `KgStageEnum` code 对齐），零 schema 变更，纯反查。

### 14. 全量知识点分页接口（学生端知识点总览）

**决策**：新增 `POST /api/kg/knowledge-points`（body `{stage, page, size}`，对齐现有 kg 接口全 POST body 风格），按学段分页列教材知识点，每项带 `kpUri`/`kpLabel`/`stage`/`chapterLabel`/`sectionLabel`。

**实现**：Mapper 反向 JOIN（`t_kg_textbook`[stage 过滤] → `t_kg_textbook_chapter` → `t_kg_chapter_section` → `t_kg_section_kp` → `t_kg_knowledge_point`）+ COUNT 分页。数据源 kg 镜像只读。

**权限**：登录即可（学生端），路径 `/api/kg`（区别于 `/api/auth/kg` 管理前缀）。

**理由**：知识点总览是"全量知识地图"底图（1000+ 条），按学段分页避免一次拉全量；`chapterLabel`/`sectionLabel` 供前端"学段→章节→知识点"二次分组。

### 15. 题型库分页 + 关联知识点接口（题型分析）

**决策**：新增两个接口：
- `GET /api/kp/question-types?page=1&size=20`：分页列题型（`id`/`topicLabel`/`status`/`hitCount` + `total`），`QuestionTypeRepository` 补 `findPage`。
- `GET /api/kp/question-types/{id}/knowledge-points`：该题型关联知识点（`QuestionTypeKpRepository.findByQuestionTypeId` 已有 + `kgKnowledgePointRepository.findByUris` 反查 kpLabel），返回 `kpUri`/`kpLabel`/`gradeRange`/`ratio`/`hitCount`。

**理由**：题型分析页需"题型库浏览 + 通过题型看关联知识点"。`QuestionType`/`QuestionTypeKp` 目前只有 `kp_uri` 无 name，`kpLabel` 从 kg 镜像反查（不冗余存 name，权威标签唯一来源 kg 镜像）。

### 16. 掌握度主体翻转：题型直接观测，知识点派生

**决策**：学生掌握的是**题型**（"鸡兔同笼"）不是**知识点**（"二元一次方程组"）——学会鸡兔同笼 ≠ 掌握二元一次方程组。因此：

- 掌握度信号主键从 `kp_key`(URI) 翻转为 `topic_key`（归一化题型名）。
- 新增 `t_student_topic_mastery`（题型掌握度）承接信号落库；知识点覆盖度改为**运行时派生**。

```
学生做题 → 题型掌握度（topic_key + 0/25/50/75 四档）
        → 题型→知识点映射（QuestionTypeKp.ratio / 未聚合时 obs 单观测 ratio=1）
        → 知识点派生覆盖度 coverage(kp) = Σ(覆盖该 kp 的题型掌握度 × ratio)
```

**`t_student_topic_mastery`（题型掌握度主表）**——结构镜像 `t_student_kp_mastery`（只存确定掌握度，`status`/`confidence` 读时从 obs 关联，不冗余落库）

| 字段 | 说明 |
|---|---|
| `id` | 主键 |
| `student_id` | 学生 |
| `topic_key` | 归一化题型标识（UNIQUE with student_id） |
| `topic_label` | 题型展示名（规范 label） |
| `mastery_level` | 0/25/50/75 四档（复用 `MasteryLevel`） |
| `evidence` | 证据（JSON：命中步骤、错误事件 id 列表） |
| `last_session_id` | 最近一次答疑会话 |
| `updated_at` | 更新时间 |

> UNIQUE(`student_id`, `topic_key`)。同生再次遇到同题型 → 取 max 单调不减（同旧 KP 掌握度策略）。
> `status`(RESOLVED/PENDING) 与 `confidence` 读时组装：RESOLVED 项来自本表 + obs 置信度；PENDING 项来自 obs（kp_uri 为空）并入「待确认」。

**理由**：题型是学生的直接认知对象（这道题会不会做），知识点是题型背后的抽象。直接观测题型 + 派生知识点，既符合认知，也避免"把无限题型硬塞到有限知识点上"导致掌握度粒度错位。知识点覆盖度是"读时计算"，不冗余落库，单一事实源仍是题型掌握度 + 题型→kp 映射。

### 17. topic_key 归一化（题型标识主键）

**决策**：题型标识用归一化后的题型名 `topic_key` 作主键，`topic_label` 只作展示。归一化函数落 domain（`TopicKeyNormalizer`），规则：Unicode NFKC 全角→半角、trim + 空白折叠、去末尾标点（"鸡 兔 同 笼" / 全角写法 / 带标点 → 同一 key）。**SHALL NOT 剥离「问题/题型」等后缀**——「相遇问题/追及问题/工程问题」里的「问题」是题型名固有部分，剥离会丢语义（同义词聚类留大数据阶段）。

**理由**：题型空间无限且命名不规整（LLM 随手输出），自由文本直接作主键会导致同题型裂成多行、掌握度分散。归一化收敛到稳定 key，又与 `t_kp_derived_obs.topic_label` / `t_kp_question_type.topic_label` 对齐（题型库晋升后按 `topic_key` 关联）。冷启动首次遇到题型即可落掌握度，无需等题型库聚合——这是选 `topic_key` 而非 `question_type_id` 外键的核心原因（外键会冷启动断裂）。

### 18. 知识点派生覆盖度计算

**决策**：`coverage(kp) = clamp(Σ_{topic→kp} (topic_mastery × ratio), 0, 75)`。

- **ratio 来源**：优先 `t_kp_question_type_kp.ratio`（聚合后跨学生分布）；该题型尚未聚合时，用 `t_kp_derived_obs` 该生单观测（topic→kp，ratio 隐式 1）。
- **coverage**：连续值 0-75（封顶，题型四档顶 75）；**masteryLevel**：离散四档（≥75→advanced / ≥50→intermediate / ≥25→beginner / 否则 0），列表与图谱着色用。两者都返回。
- **status/confidence**：取覆盖该 kp 的题型中最高 confidence；存在任一 `status=PENDING` 的题型则整项标疑似态。

**理由**：覆盖度是"该知识点被学生已掌握题型覆盖的程度"，连续值供详情展示、离散档供图谱着色。封顶 75 与题型四档顶对齐，避免多个题型叠加同一 kp 时溢出成无意义高分（多题型覆盖同 kp 的叠加语义留待大数据阶段细调，本期 clamp 保守）。

### 19. 掌握度接口改造 + 派生覆盖度接口

**决策**：拆两个接口，对应前端「掌握度」（题型四类明细）与「知识点总览」（派生覆盖度着色）：

- ① **改造** `GET /api/students/{id}/mastery` → 返回题型掌握度 `items[] { topicKey, topicLabel, masteryLevel, status, confidence, updatedAt }`。
- ② **新增** `GET /api/students/{id}/kp-coverage` → 返回知识点派生覆盖度 `items[] { kpUri, kpLabel, coverage, masteryLevel, status, confidence, stage, chapterLabel, sectionLabel }`。
- ③ 已实现保留：`POST /api/kg/knowledge-points`（全量知识点分页）、`GET /api/kp/question-types`（题型库分页）、`GET /api/kp/question-types/{id}/knowledge-points`。

**理由**：题型掌握度与知识点覆盖度是两个不同粒度视图（一个按题型、一个按知识点），拆开各自清晰。`stage`/`chapterLabel`/`sectionLabel` 从 mastery 移入覆盖度接口（这些是知识点的归属属性，题型无归属语义）；`kpLabel` 反查沿用 kg 镜像（权威标签唯一来源）。

### 20. 迁移策略：并行保留 + 派生覆盖

**决策**：旧 `t_student_kp_mastery`（student_id + kp_key）**本期保留不动**，错题本/既有掌握度查询不受影响；新增 `t_student_topic_mastery` 承接新题型信号。知识点覆盖度查询顺序：**优先题型派生** → 无题型映射的 kp 回退旧 KP 掌握度（过渡期兜底）→ 随题型库覆盖率提升逐步弱化旧表依赖。旧表归档/删除列为后续（需大数据侧 + 覆盖率达标后），本期不删。

**理由**：翻转是主键语义变更，一次性迁移破坏面大（错题本、掌握度追踪、历史数据）。并行两表 + 读时派生，可灰度、可回退、不锁旧链路；题型侧数据自然积累到覆盖旧表后，再择机下线旧表。

### 21. 冷启动 LLM 消歧：LLM 生成候选名 + 镜像校验

**决策**：现 `KpLlmDisambiguator` 候选只来自 `findByLabelLikeList(label)`（镜像知识点名 LIKE），题型名（"鸡兔同笼"）在知识点名里 LIKE 不到 → 候选空 → LLM 不被调用 → 冷启动断、题型库长不出来。改为**两段式**：

```
③ LLM 消歧（冷启动，题型库无先验时）
  1. LLM 生成候选名：给定题型 label + 年级上下文，LLM 自由生成 N 个候选知识点名（"二元一次方程组"/"假设法"...）
  2. 镜像校验：Java 用 findByLabel(exact) / findByLabelLike(LIKE) 回镜像校验，命中才保留
     → 单候选命中 → RESOLVED（仍标 WEAK，见 Decision 9）
     → 多候选命中 → PENDING + 候选列表，弹澄清卡给学生选
     → 零命中 → PENDING（无候选，纯挂起）
```

**理由**：题型名和知识点名是两套词汇，靠「知识点名 LIKE 题型名」召回候选是死路。LLM 有跨词汇语义能力，能"由鸡兔同笼想到二元一次方程组"；但 LLM 会幻觉，所以候选名必须回镜像校验，最终 kp 必在镜像。这不算违背 Decision 2 的「SHALL NOT 凭空生成 kp」——LLM 只生成 **name 候选**，kp 本身经镜像校验存在。

**冷启动弱化沿 Decision 9**：首条 LLM 消歧标 `WEAK`，第二独立信号（第二名同学共现 / 学生投票达标 / 做题结果佐证）才转 RESOLVED。

### 22. 离线聚合升级：LLM 自动关联题型↔知识点

**决策**：现 `KpQuestionTypeAggregationService` 是纯计数聚合（同名题型命中≥N 建 CANDIDATE），冷启动慢、也无法纠错 LLM 误关联。升级为**计数 + LLM 自动关联**：

- **输入**：达阈值的题型名 + obs 共现的 `(kp_uri, 命中次数, 年级分布桶)`。
- **LLM 输出**：规范化的「题型 → kp 分布（ratio 归一化和=1）」+ 置信度。
- **产出**：建/更新 `t_kp_question_type` + `t_kp_question_type_kp`（CANDIDATE）。

**冷启动弱化沿 Decision 9**：LLM 关联结果不直接 STABLE；第二独立信号（多名学生共现 / 学生投票达标 / 做题结果佐证）才升 STABLE 进解析先验。LLM 只做「提名」，确定性靠「重复 + 客观信号」。

**归属**：`batch` 包（离线，大数据归宿），与 Decision 11 一致。

**理由**：题型库要「自我生长」而非初始化灌数据——在线阶段学生/LLM 把题目和知识点关联成 obs，离线阶段 LLM 从 obs 共现里归纳出可靠的题型→知识点映射，题型库逐步补充。这样第 0 天无题型库也能跑，靠 LLM 消歧冷启动 + 离线聚合慢慢长满。

## Risks / Trade-offs

- [冷启动种子依赖 LLM] → 题型库空时第一次关联只能靠 LLM。缓解：学生澄清意图（可选）+ 单学科（数学）+ label 接地（复用 mastery_snapshot 已知 label）降噪。
- [LLM 生成候选名幻觉] → 冷启动消歧让 LLM 自由生成候选名，可能生成镜像不存在的知识点。缓解：候选名必经镜像 exact/LIKE 校验（最终 kp 必在镜像）+ WEAK 弱化（不直接点亮）。
- [离线 LLM 聚合误关联] → LLM 归纳题型→知识点可能把共现误判为因果。缓解：第二独立信号才升 STABLE + 审核门禁 + 分布异常重审。
- [LLM 自证循环 / 高置信幻觉] → LLM 用自身偏见确认自身偏见、自信地错（给高置信但选错）。缓解：LLM 判断强制接客观信号校准（学生意图/做题结果/多模型交叉），不全闭环自证。
- [开发者打标脱离解题] → 人工兜底若做"日常打标"会因脱离真实解题而不可靠。缓解：人工降级为极少数边界仲裁，且找懂学科的人。
- [学生恶意/乱点投票] → 学生澄清可能被故意答错。缓解：只碰学科概念不碰 kp_uri、只影响自身观测、票数稀释、≥3 人一致才进候选、跳过即弃权。
- [题型库噪音聚合] → 阈值 + 审核门禁 + 保守自动修正；分布异常触发重审。
- [学生年级不可得] → 降级为纯 LLM 消歧（无年级锚），置信度下降。
- [obs 长期尾膨胀] → 同生同题型去重计数 + 聚合后原观测按需归档（未来分表/清理）。
- [错解析污染掌握度] → 打标 MIGRATED + 人工复核，不自动删。
- [维护任务误改] → 保守原则：高置信才自动改，否则 HUMAN_REVIEW。

## Migration Plan

1. Flyway 迁移新增 4 表（`ai_edu_learning`）：`t_kp_derived_obs`、`t_kp_question_type`、`t_kp_question_type_kp`、`t_student_topic_mastery`。
2. 掌握度主体翻转灰度：`applyMasteryAndErrors` 改落题型掌握度 + 派生覆盖度接口；旧 `t_student_kp_mastery` 保留并行，覆盖度查询无题型映射时回退旧表。
3. 解析管线灰度：先只升级解析逻辑 + 落 obs（不接点亮），验证解析质量后再接点亮。
4. 学生端图谱页新路由，不动 admin 图谱页（复用组件，双入口）。
5. 维护闭环最后上线（依赖 obs/题型库稳定）。回滚：停维护任务 + 关闭学生图谱路由即回退。

## Open Questions

0. **【高优先级·跨仓库协调】Python `mastery_signals` 信号源粒度**：现状 `kp_label` 是自由文本（题型/知识点混合，见 Context），要翻题型粒度需 Python 稳定输出**题型 label**。字段名 `kp_label` 是否重命名为 `topic_label`？（默认：建议重命名 `topic_label` 语义清晰，Java `MasterySignalItem` 对应改 `@JsonProperty`；Python 未就绪前 Java 侧兼容旧字段名 `kp_label` 作为过渡）。
1. **student_grade 来源**：组织系统查（学生→班级→年级）还是 `DecideRequest` 加 `student_grade` 契约字段？（默认：Java 解析时查组织系统，不改 Python 契约）。
2. **LLM 消歧调用方式**：复用 `llm-gateway`（Java 侧小调用）还是新增 Python 消歧端点？（默认：llm-gateway，避免动 Python）。
3. **聚合阈值初值**：CANDIDATE≥3 / STABLE≥10（默认采纳，可配置）。
4. **掌握度自动迁移**：本期只打标，是否后续做自动迁移？（默认：本期不做）。
5. **消费方**（变式题/错题分组）本期不做，题型库先沉淀数据。
6. **澄清卡数据契约**：候选概念 + 低置信状态从哪来——SSE meta 扩展，还是前端单独调 `POST /api/kp/resolve`？（默认：前端单独调 /api/kp/resolve，接口已返回 candidates，不改 decide meta + Python 契约）。
7. **topic_key 归一化力度**：字面归一化（全角半角/空白/去末尾语气词）初版是否够用，是否需同义词聚类（"鸡兔同笼"≈"鸡兔问题"）？（默认：本期只做字面归一化，同义词聚类留大数据阶段）。
