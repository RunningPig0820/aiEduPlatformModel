# kp-question-analysis 技术设计

## Context

- **老方案已就绪**（`kp-matching-lightup-frontend`）：题型库聚合任务（`KpQuestionTypeAggregationService`，凌晨 3:17 扫 obs → 沉淀 `QuestionType`/`QuestionTypeKp`）、题型库分页 + 关联知识点接口、`vote` 接口（落 `STUDENT_VOTE` 观测）、`resolve` 接口（label → 知识点解析，PENDING 返回 candidates）。
- **聚合任务已消费学生确认**：`selectResolved()` = `WHERE kp_uri IS NOT NULL`（不看 source），学生 `vote` 落 `RESOLVED + STUDENT_VOTE` 观测（kp_uri 非空），天然进聚合 → 跨学生达阈值（≥3 学生 / ≥5 命中）沉淀题型库。
- **现有接口**（复用）：`POST /api/tutoring/ocr`（拍题识别文本）、`GET /api/kp/question-types`（题型库分页）、`GET /api/kp/question-types/{id}/knowledge-points`（题型→知识点）、`POST /api/kp/vote`。
- **缺口**：`resolve` 是 **label 级**（需先知道题型名）；题目理解只在答疑 Python `decide` 内（SSE 会话绑定）。无「题目文本 → 识别题型 → 关联知识点」的独立 REST 接口。

## Goals / Non-Goals

**Goals:**
- 智能练习下「题型分析」页：贴题/拍题 → 单题分析（识别题型 → 关联知识点清单）。
- 学生可在题型分析页「确认/纠正」题型↔知识点关联 → 落 `student_vote` → 喂聚合任务（产品流程闭环）。
- 先纯分析展示；掌握度标注接口预留。

**Non-Goals:**
- 管理端/老师端全局审核（`kp-pending-review`）本期不做，学生确认只走个人观测。
- 掌握度标注第一版不做（`kp-coverage` 数据到位后叠加，接口预留）。
- 不动老方案已收口的掌握度/知识点总览/澄清卡行为。
- 聚合任务本身不改（已消费 STUDENT_VOTE；手动触发/source 加权为可选后续）。

## Decisions

### 1. 单题分析 = 独立 `analyze-question` 端点（从 decide 拆出「题目理解」，非整个 decide）

新增 `POST /api/kp/analyze-question { text }`，响应 `{ topicLabel, status, confidence, knowledgePoints: [{kpUri, kpLabel, gradeRange, ratio}] }`（PENDING 时 knowledgePoints 空 + candidates）。

理由：单题分析是**无状态一次性请求**（贴题→结果），答疑是**多轮 SSE 会话**，交互模型不同，不该绑会话。独立端点 = 独立「题目→题型/知识点」能力，答疑/练习/题型分析多入口复用。实现复用 resolve 管线的题型识别（镜像 → 题型库 → LLM 消歧），把「题目理解」从 Python decide 拆出为独立调用，而非复用整个 decide 流程（decide 还含引导策略/护栏）。

### 2. 学生确认 = 复用 `vote` 接口，喂聚合任务（不新设计）

题型分析页「确认关联」直接复用 `POST /api/kp/vote { topicLabel, selectedLabel }` → 落 `STUDENT_VOTE + RESOLVED` 观测，并**即时转正该生该题型的 PENDING obs**（待确认清单随之消失）。聚合任务已消费该源（`selectResolved` 扫 kp_uri 非空），跨学生达阈值自动沉淀题型库。

**两个确认入口（方案 a）**：
- **贴题结果确认**：RESOLVED 知识点行、PENDING 候选，均可点「确认」→ vote。
- **待确认清单确认（方案 a）**：掌握度页 pending-kps 待确认项展开候选，每条可「确认」→ vote 转正。复用同一 vote 接口，接口不变，纯前端交互。

理由：**不重复造轮子**——`vote` 链路（含记录 `occurrence_count` 幂等、转正 PENDING、喂聚合）已通，题型分析页与待确认清单只是它的消费入口。这与澄清卡同底层，多入口复用同一能力。方案 a 使 PENDING 态永远可操作（能选、能 vote），不是死胡同。

后端确认：candidates 已做镜像校验，每个候选都能 vote（正常不触发 10003）。

### 3. 展示 = 先纯分析（题型 + 关联知识点清单），掌握度标注预留

单题分析结果展示「题型 + 关联知识点（kpLabel + 年级分布 + 占比 ratio）」清单。掌握度标注（叠加「你已掌握/待巩固」）第一版不做，但前端数据层预留：`analyze-question` 返回 kpUri，前端可查 `kp-coverage` 的 `coverageMap` 有则标、无则灰，待数据到位自然点亮。

**PENDING 分支需处理两种**：后端 WEAK（LLM 冷启动猜测）现在也返回 `PENDING`（不再冒充 RESOLVED），故 PENDING 出现频率变高，需同时处理「有 candidates（可确认）」与「candidates 空（仅空态提示）」。

理由：现在 `kp-coverage` 数据是空的（题型掌握度表空），第一版标了也全是灰。先跑通「贴题→分析→展示」主流程。

### 4. 菜单 = 智能练习（一级翻 active）→ 题型分析（二级子菜单）

```
智能练习（一级，pending 翻 active，可折叠父项）
  └─ 题型分析（二级页面，/student/practice/question-analysis）
```

与「学习报告 → 掌握度/知识点总览」同构（Sidebar `SubMenuItem` 已支持）。理由：用户要求子菜单结构、页面统一；将来智能练习再出「出题练习」功能时平级加子项即可。

### 5. 复用与范围收敛

- OCR（图片题）→ 复用 `POST /api/tutoring/ocr`。
- 题型库浏览（聚合结果展示）→ 复用 `GET /api/kp/question-types` + `/{id}/knowledge-points`。
- 本方案**不新增**题型→知识点关联表/任务，全部消费既有；唯一后端新增是 `analyze-question`。

### 6. 存疑挂起闭环（后端已交付，2026-08-17 联调后新增）

后端 `kp-question-analysis-backend` 已交付「存疑挂起 → 学生选择/后续任务补充」闭环，前端契约增强（**无破坏性变更**）：

```
学生贴题 → analyze-question
  ├─ 权威命中（题型库/镜像）→ status=RESOLVED，展示关联知识点
  └─ 存疑/冷启动 → status=PENDING，candidates（保证可 vote）
                  + 后端自动落 PENDING obs「挂起来」（进 pending-kps，不丢）
      ├─ 学生选候选 → vote → 该 PENDING 转正 RESOLVED → 跨学生达阈值沉淀题型库
      └─ 学生不选 → 后端维护任务 LLM 重判 → 转 WEAK → 共现转正
```

**后端行为变更（前端需知晓）：**
- **WEAK 降级**：冷启动 LLM 猜测（曾返回 RESOLVED conf=70）现在**返回 PENDING**——只作为候选待确认，不再冒充权威答案。PENDING 态出现频率变高，前端按 PENDING 分支处理（有 candidates / 空 candidates 两种）。
- **candidates 镜像校验**：analyze 返回的候选全部经后端 kg 镜像校验，**vote 不会报 10003**。
- **vote 转正**：vote 成功会把该生该题型的 PENDING obs 转正为 RESOLVED（待确认清单即时消失），提示「已记录，将参与题型整理」（跨学生达阈值才沉淀题型库，非即时）。
- **确定性**：后端用「全候选遍历（顺序无关）+ 提示词收敛 + 数据锚优先」，不依赖缓存；status 稳定，candidates 冷启动下可能波动（预期）。

**前端新增面（tasks 组 8）：** ① PENDING 候选可点投票（核心）；② `pending-kps` 待确认清单加「确认」交互（方案 a，复用 vote，需产品确认）；③ 题型库空态文案；④ WEAK 降级适配回归。

### 7. 待确认清单候选来源 = 复用 `resolveKp` 现取（方案 A）

`PendingKpAliasDTO` **不含 candidates 字段**（仅 id/topicLabel/confidence/status/kpUri/kpLabel/…）。8.2 待确认清单确认交互的候选来源决策：

- **方案 A（选定）**：前端展开待确认项时，纯 PENDING 项调 `POST /api/kp/resolve { label: topicLabel }` 现取 candidates（复用既有接口，零后端改动）；WEAK 项自带 kpLabel 直接可确认。
- 方案 B（不选）：后端给 pending-kps 每条补 candidates 字段（接口增强，可后续优化）。

理由：`resolveKp` 已通（澄清卡同底层），先前端跑通闭环；后端加字段是低价值优化，等确认频率高时再做。

### 8. PENDING 空候选 → 知识点搜索确认（后端加 keyword 搜索，2026-08-17 新增）

实测冷启动题型（鸡兔同笼）analyze/resolve 均返回**空候选**，PENDING 空态是死胡同——学生无法主动确认。方案：**后端给 `POST /api/kg/knowledge-points` 加可选 `keyword`**（有 keyword 时跨学段按 label 搜索，无 keyword 保持原分页行为），前端 PENDING 空态 + 待确认清单空候选时提供「搜索知识点」选择器：

```
暂无法确认关联知识点
  🔍 搜索知识点…（实时搜，防抖）
  ○ 用适当方法解二元一次方程组   ← 选中
  ○ 鸡兔同笼问题
  [确认所选知识点] → vote(topicLabel, kpLabel)
```

选中项来自知识图谱镜像（`listKnowledgePoints` 返回的 kpLabel），**天然满足 vote 的 findByLabel 校验，不会 10003**。

理由：候选空 = 后端 LLM/镜像冷启动猜不出，但教材知识图谱里有对应知识点（如「用适当方法解二元一次方程组」）——搜索是「机器猜不出，学生自己指」的兜底，把 PENDING 死胡同变成可操作路径。后端改动极小（一个可选 keyword 参数），前端搜索框可复用（题型分析空态 + 待确认清单两处）。

> ⚠️ **范围降级（2026-08-17）**：决策 2/6/7/8（学生确认 vote、存疑挂起闭环、待确认清单确认、搜索选择器）**转后续独立功能，本期不在题型分析入口承担**。见决策 9。

### 9. 范围降级：题型分析 = 题型识别 + 知识点顺带展示（确认/完善转后续）

**核心业务关系（本期定位）**：题目 ↔ 题型（题目归题型）；题型 ↔ 知识点（题型关联知识点）；掌握度 = 掌握哪些题型。

- **题型分析页 = 贴题 → 识别题型**（核心产出）；知识点是 LLM **顺带判断**的参考——有则展示，无则不强求（不报错、不做确认闭环）。
- **不做**（转后续独立功能）：学生确认关联（vote 喂聚合）、候选搜索选择器、待确认清单确认交互、题型↔知识点完善。这些属于「在应用入口完善关联」，本期由独立功能（管理端审核/专项）承接。
- **知识点总览页**（老方案）保留为展示入口（暂不完善，供演示）。

理由：题型识别可靠（实测 4/4 识别正确）；题型↔知识点关联是 LLM 冷启动难项，**不应阻塞本期题型分析主流程**。降级后：学生贴题必得「题型」结果，知识点作为参考锦上添花——流程顺畅、不空白焦虑、不留死胡同。

**已实现代码处置（方案甲）**：题型分析页已实现的候选确认/搜索选择器/待确认清单确认交互**保留代码但不作为本期承诺需求**（页面更完整，独立功能将来直接复用）；方案 scope 按降级执行。

## Risks / Trade-offs

- [analyze-question 依赖 LLM 可用] → 题目理解走 LLM，服务不可用/低置信时返回 PENDING + candidates（同 resolve 契约），前端渲染空态 + 提示，不阻塞。
- [学生确认冷启动阈值] → 单学生确认不立即生效（聚合需 ≥3 学生/≥5 命中）。缓解：前端「确认成功」提示 + 说明「已记录，将参与整理」，避免学生以为立即改全局。
- [candidates 内容冷启动波动] → 后端已确认：status 稳定（无数据锚恒 PENDING），但 candidates 内容可能波动（属预期）。前端容忍空结果 + 渲染动态候选。
- [vote 10003] → 后端已做 candidates 镜像校验，正常不触发；前端仍兜住（toast + 复位可重试）。
- [PENDING 题型无知识点] → analyze-question 低置信时只有 candidates 无 knowledgePoints，前端展示「待确认」候选 + 让学生选（走 vote）。
- [WEAK → PENDING 频率变高] → 冷启动猜测不再冒充 RESOLVED，PENDING 分支是常态路径，需覆盖「有 candidates」与「空」。

## Migration Plan

1. 后端 `analyze-question` 端点（从 resolve 管线加「题目理解」前置，或独立复用识别能力）。
2. 前端 API 封装：`analyzeQuestion(text)`。
3. 智能练习菜单翻 active + 挂「题型分析」子菜单 + 路由。
4. 题型分析页：贴题输入 + 结果清单 + 确认交互（复用 vote）。
5. 联调：贴题 → 分析 → 展示 → 确认 → 查 obs 落库 → 聚合（手动/次日）。
6. 回滚：关掉「智能练习」路由即回退，不碰后端。

## Open Questions

<!-- 已全部关闭。 -->

> 已关闭：
> - **菜单形态**：子菜单——智能练习（一级）→ 题型分析（二级），页面统一。
> - **结果展示**：先纯分析（题型 + 关联知识点清单）；掌握度标注预留（数据到位自然亮）。
> - **后端 analyze-question**：独立一次 LLM 题目理解调用（从 decide 拆出，非整个 decide），无状态可复用。
> - **学生确认归属**：个人观测（`student_vote`），喂聚合任务；全局审核（管理端）另开功能点。
> - **聚合整理**：已存在且消费 STUDENT_VOTE，本方案只加确认入口，不新设计。
> - **pending-kps 确认交互（方案 a/b）**：确认选 **方案 a**——待确认清单每条展开候选可「确认」（复用 vote 转正，接口不变），学生贴题时与事后清单里都能补，闭环完整。
> - **candidates 校验**：后端确认 candidates 已镜像校验（正常 vote 不 10003）。
> - **WEAK 语义**：后端确认 WEAK 也返回 PENDING（不再冒充 RESOLVED），前端 PENDING 分支需覆盖「有/无 candidates」。
> - **待确认清单候选来源（A/B）**：选 **方案 A**——`pending-kps` 不含 candidates，前端展开时复用 `resolveKp(topicLabel)` 现取；WEAK 项自带 kpLabel 直接可确认。后端加字段（方案 B）留后续。
> - **PENDING 空候选确认路径**：选「后端加搜索接口」——`POST /api/kg/knowledge-points` 加可选 `keyword`，前端空态提供「搜索知识点」选择器，选中镜像知识点 → vote（保证可 vote 不 10003）。
