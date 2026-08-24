# 智能练习 · 题型分析（贴题 → 题型识别 + 知识点参考）

## Why

老方案 `kp-matching-lightup-frontend` 已把「题型→知识点关联」链路做完：后端定时任务 `KpQuestionTypeAggregationService` 从个体观测沉淀题型库（`QuestionType`/`QuestionTypeKp`），题型库分页 + 关联知识点接口已就绪。但消费端是「浏览型」——学生只能分页看题型库，**没有「贴一道题 → 识别出它是什么题型」的入口**。

**核心业务关系**：题目 ↔ 题型（题目归题型）；题型 ↔ 知识点（题型关联知识点）；掌握度 = 掌握哪些题型（不直接追知识点）。

**范围降级（2026-08-17）**：本期题型分析页只做**「贴题 → 识别题型」**，知识点是 LLM **顺带判断**的参考——**有则展示，无则不强求**（不报错、不做确认闭环）。题型↔知识点关联的「确认/完善/校准」**不在应用入口做**，留给后续独立功能（管理端审核/专项完善）。老方案的「知识点总览」页保留为展示入口（暂不完善）。

## What Changes

- **智能练习**（一级菜单，pending 翻 active）下新增**「题型分析」子页**：贴题/拍题/粘贴图片 → `analyze-question` → **识别题型**（核心产出）+ LLM 顺带给出的关联知识点（有则展示，无则空态，不阻塞）。
- **知识点展示**：RESOLVED 展示题型 + 关联知识点清单；PENDING 展示「待确认」态（若 LLM 给出候选可展示，候选为空仅提示，**不要求必有关联**）。
- **题型库浏览**：复用 `GET /api/kp/question-types` + `/{id}/knowledge-points` 分页展示聚合沉淀结果。
- **后端新增 `POST /api/kp/analyze-question`**：题目文本 → 独立「题目理解」调用 → 返回题型 +（可选）关联知识点。
- **不做（转后续独立功能）**：学生确认关联（vote 喂聚合）、候选搜索选择器、待确认清单确认交互——本期不在题型分析入口承担「完善题型↔知识点关联」职责。
- **复用**：`POST /api/tutoring/ocr`（拍题识别）、`GET /api/kp/question-types`、`GET /api/kp/question-types/{id}/knowledge-points`。

## What Changes

- **智能练习**（一级菜单，pending 翻 active）下新增**「题型分析」子页**：贴题/拍题 → `analyze-question` → 识别题型 → 展示关联知识点清单（纯分析）。
- **学生确认交互**：结果卡片每条知识点（RESOLVED）或候选（PENDING）可「确认关联」→ 复用 `POST /api/kp/vote` 落 `STUDENT_VOTE` 观测（不污染全局，跨学生达阈值后由聚合任务沉淀）。
- **后端新增 `POST /api/kp/analyze-question`**：给定题目文本 → 独立「题目理解」调用（从答疑 Python `decide` 拆出识别题型能力，非整个 decide）→ 返回题型 + 关联知识点。
- **复用**：`POST /api/tutoring/ocr`（拍题识别）、`GET /api/kp/question-types`（题型库分页）、`GET /api/kp/question-types/{id}/knowledge-points`（题型→关联知识点）、聚合任务（已消费 STUDENT_VOTE）。

## 后端契约确认（2026-08-17，后端转前端）

产品闭环（核心逻辑）：贴题 → `analyze-question` → 权威命中 `RESOLVED`（展示关联知识点）/ 存疑·冷启动 `PENDING`（展示候选 candidates + 后端自动落一条 PENDING obs 进待确认清单，不丢）。

- **WEAK → PENDING**：WEAK（LLM 冷启动猜测）现在也返回 `PENDING`，不再冒充权威 `RESOLVED`——前端需按 PENDING 分支处理「有 candidates」和「candidates 空」两种。
- **candidates 已镜像校验**：每个候选都能 vote，正常不触发 10003。
- **status 稳定**：同文本多次调用 status 稳定（无数据锚时恒 PENDING）；candidates 内容冷启动下可能波动，属预期。
- **analyze 纯分析不写观测**，但存疑自动落 PENDING obs 进待确认清单。
- **vote 成功** → 该生该题型 PENDING obs 转正 RESOLVED（待确认清单即时消失）；**vote 失败 10003** → toast + 复位可重试。
- **pending-kps**：现在包含 analyze 存疑新落的 PENDING obs（此前只有答疑挂起的），每条 `{ id, topicLabel, status, confidence, kpUri, kpLabel, ... }`。
- **待确认清单确认交互（方案 a）**：掌握度页待确认项加「确认」交互，复用 vote 转正——学生不仅能贴题时选，还能事后在清单里补，闭环更完整。
- **题型库空态文案**：`question-types` total=0 时提示「题型库随学生做题与确认逐步积累」，非 bug。
- **前端契约确认**：axios 超时 30s（LLM 冷调用慢）、confidence 0-100、candidates 字符串数组。

## Capabilities

### New Capabilities

- `kp-question-analysis`: 智能练习下题型分析——贴题 → 识别题型（核心）+ LLM 顺带知识点参考（有则展示无则不强求）。掌握度标注预留。学生确认关联/搜索完善 **转后续独立功能**（本期不在应用入口做）。

### Modified Capabilities

- 复用老方案 `kp-matching-lightup-frontend` 的 `kp-question-type-analysis` 接口（题型库分页 + 关联知识点），本方案不改其行为，仅新增消费入口。

### 后续（本期不做）

- 管理端/老师端**全局审核**题型↔知识点（`KpAliasReviewController` 已就绪，`kp-pending-review`）：独立新功能点，学生确认仅走个人观测、不改全局。
- 掌握度标注（单题分析结果叠加「你已掌握/待巩固」）：接口预留，待 `kp-coverage` 数据到位后叠加。
- 聚合任务手动触发 + source 加权（学生确认权重高于 LLM）：可选增强。

## Impact

- **前端（主）**：新建 `src/pages/student/QuestionAnalysis.jsx`（贴题/拍题/粘贴图片 → 题型识别 + 知识点展示）；`routes.jsx`/`constants` 学生菜单「智能练习」翻 active 并挂「题型分析」子菜单 + 新路由；`tutoring.js` 补 `analyzeQuestion` 封装。
- **后端（配合）**：新增 `POST /api/kp/analyze-question {text}`（独立题目理解，复用 resolve 管线的题型识别 + 题型库关联）。`ocr`/题型库接口已就绪不动。
- **数据契约**：`analyze-question` 请求 `{ text }`；响应 `{ topicLabel, status, confidence, knowledgePoints: [{ kpUri, kpLabel, gradeRange, ratio }] }`（PENDING 时 knowledgePoints 为空 + candidates，**candidates 可空，前端不强求关联**）。
- **不做（转后续）**：`vote` 确认闭环、候选搜索、待确认清单确认交互。
