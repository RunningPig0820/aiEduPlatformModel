# kp-question-analysis-backend 变更提案

## Why

前端「题型分析」页需要「贴一道题 → 识别题型 → 关联知识点」的独立入口。现有 `POST /api/kp/resolve` 是 **label 级**（需先知道题型名），「题目文本 → 题型名」的题目理解只在答疑 Python `decide` 会话内，无独立 REST。同时题型库按 `topic_label` **逐字聚类**，相似题型叫法不一（「鸡兔同笼」vs「鸡兔同笼问题」）会裂成重复条目、稀释聚合阈值（≥3 学生/≥5 命中被劈开），学生确认 vote 的 topicLabel 也会落成重复题型。

前提：**没有现成完整的知识点/题库标注表**，知识点用 TextbookKP URI 锚定（kg-sync 镜像），题型→知识点关联靠 LLM + 观测闭环 bootstrap。本 change 补齐产品闭环的入口（贴题分析）与题型库健康机制（别名合并）。

## What Changes

- **新增 `POST /api/kp/analyze-question { text }`**：题目文本 → Java 自研题目理解（LLM 生成候选题型名 + 镜像校验）→ 题型名 → 复用解析管线（镜像 → 题型库 → LLM 消歧）→ 返回关联知识点清单 `{ topicLabel, status, confidence, knowledgePoints: [{kpUri,kpLabel,gradeRange,ratio}], candidates }`。**权威命中不写 obs；存疑 PENDING 落一条 PENDING obs「挂起来」**（去重，进待确认清单，供学生选择/维护任务补充，存疑不丢）。PENDING 不报错、携带澄清候选（已镜像校验，可 vote）。
- **存疑挂起闭环（联调后定稿）**：存疑 → PENDING obs → 学生 vote 转正（`resolvePendingByStudentTopic`）/ 维护任务 LLM 重判（`rejudgePending` → WEAK → 共现转正）→ 聚合沉淀题型库。确定性靠全候选遍历 + 提示词收敛 + 数据锚优先（**非缓存**）；LLM 消歧预算前 2 候选；聚合排除 WEAK 防幻觉污染；WEAK 结果降级为 PENDING 候选待确认。
- **新增题目理解端口**（domain）：`QuestionUnderstandingPort`，默认 Java LLM 实现（`KpQuestionAnalyzer`）；Python 独立端点（拆 decide 题目理解）作为可替换实现，端口预留、本期不做。
- **新增题型库别名合并**：`t_kp_question_type_alias` 别名表 + 聚合时按 kp_uri 集合重叠（≥70%）把变体题型并入 canonical 题型（别名 + 观测折叠）+ `findByTopicLabelOrAlias`。让「鸡兔同笼」/「鸡兔同笼问题」收敛到同一题型条目、同一 kp 分布，resolve②与 vote 均按别名命中。
- **解析管线②升级**：`resolveByCatalog` 由精确 `findByTopicLabel` 改 `findByTopicLabelOrAlias`，相似题型命中同一先验。
- **复用不动**：`POST /api/kp/vote`（学生确认落 STUDENT_VOTE，现含转正 PENDING）、`POST /api/tutoring/ocr`（拍题）、`GET /api/kp/question-types` + `/{id}/knowledge-points`（题型库浏览）、聚合任务（消费 STUDENT_VOTE）均已有。

**第二轮（2026-08-17 联调后）——封闭域约束选择（P0）**：从「开放域自由猜测」→「封闭域约束选择」。题型库 miss 时，取学生学段知识点 label 池 → LLM **只能从池里选**最相关 1-3 个（恒非空，跨学段错误被池过滤消灭）。配套：`POST /api/kg/knowledge-points` 支持 keyword 搜索兜底（前端 KpSearchSelector 已就绪）；聚合手动触发（P1）；管理端审核页（P2，后续）。

## Capabilities

### New Capabilities

- `kp-question-analysis`: 贴题分析——题目文本 → 识别题型 → 关联知识点清单；学生确认关联（复用 vote）；纯分析不写 obs，PENDING 携带澄清候选。

### Modified Capabilities

- `kp-topic-resolution`: 解析管线新增题目理解前置（题目文本 → 题型名），`analyze-question` 与答疑共用同一解析能力；题型库命中由精确改别名。
- `kp-question-type-catalog`: 题型库聚合新增变体合并（kp 分布重叠 → canonical + 别名），相似题型名不再裂成重复条目、阈值不再被稀释。

## Impact

- **接口**：新增 `POST /api/kp/analyze-question`；`resolve`/`vote`/题型库分页/关联知识点接口契约不变。
- **数据**：新增 `t_kp_question_type_alias` 迁移（learning 库，`alias_label` UNIQUE + `question_type_id` FK）；`t_kp_question_type`/`t_kp_question_type_kp` 不变。
- **代码**：domain 新增 `QuestionUnderstandingPort` + `KpQuestionAnalyzer`（infra LLM 实现）+ `QuestionTypeAlias` 实体/仓储；application 新增 `KpQuestionAnalysisAppService`、改 `KpAppService`（analyze-question）、`KpQuestionTypeAggregationService`（别名合并）；interface 改 `KpResolutionController`（加端点）。
- **依赖**：无新外部依赖；题目理解复用 `LlmGateway` + `KgKnowledgePointRepository` 镜像校验。
- **边界**：管理端全局审核（`kp-pending-review`）不在本期；题库域已有题型标签当种子（跨来源观测）与批量扫题库自动补题型（proactive）为后续阶段，本期仅别名合并兜底词汇分歧。
