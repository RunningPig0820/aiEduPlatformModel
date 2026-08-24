## Why

掌握度 = 题型已确立（`kp-matching-lightup` 翻转 + `kp-question-analysis` 贴题识别），但数据底盘是**零散观测**：`decide` 逐轮输出三档信号（mastered/practicing/struggling），取 max 单调不减，算不出「某题型练了几道、答对几道」；题型名是 LLM 自由文本，「一元二次方程」和「解一元二次方程」在掌握表裂成两行。需要把掌握度升级为**以题目为单位的完整采集链路**：题目落库 → 题型名向量归一 → 累计平均正确率聚合 → 可追溯展示。

## What Changes

- **题目采集表（事实源）**：新增题目记录表，AI 答疑、题型分析页的题目全量落库（来源 ai，题库 bank 预留），记录题目文本、题型名、对错信号、引导轮数。
- **掌握信号跟题目走**：每道题一次作答一条信号——直接答对 1.0 / 引导后答对 0.5 / 答错 0.0，per-题型前几题打折（70/80/100，系数可配置）。引导轮数复用会话 `roundCount`/`answerRequestCount` 现有资产，**Python 零改动**。
- **题型动态聚集（零锚点，BREAKING 相对「按原文裂行」）**：无题库、无预置分类——canonical 由第一条相似题动态涌现。题型名在落库前聚集：字符级规则（免费处理「解X/求X」高频变体）+ 向量库最近邻（**题型名向量单信号**——本期只存题型名向量、题目向量不落库（Python 契约对齐 Non-Goals），≥阈值 → canonical 并写别名表，否则建新 + 题型名向量入库），批量聚集手动触发兜底历史散名。掌握表 key = canonical，源头不裂行。向量库独立于 MySQL（COS Vector Bucket，选型见 design）。
- **掌握度累计平均（BREAKING 相对 max 单调不减）**：`new = old × n/(n+1) + score × 1/(n+1)`，`trainCount += 1`，`source` 标记 ai/bank。一次作答算一次（不题目去重）。折扣系数/信号映射做成可配置项，支持后续变更。
- **`getMastery` 契约变更（BREAKING）**：`masteryLevel` 从离散四档（0/25/50/75）改为**连续百分比** 0-100，`items[]` 加 `source`、`trainCount`。前端分桶保留四档视觉。
- **按题型查题目列表接口**：新增「该生该题型下题目列表」（内容、对错、时间），供掌握度页「查看题目」跳转。
- **知识点总览断联（本期明确收窄）**：本期不做题型↔知识点关联；`kp-coverage` 接口保留但前端不消费，知识点总览仅展示知识地图。
- **相似题检索不做**：题目向量本期不落库（后续独立功能），本期向量库只存「canonical 题型名 → 向量」。
- **本期只记录「题目→题型」，与「题型→知识点」解耦**：掌握度链路只消费题目记录与向量聚集；`t_kp_derived_obs`/`t_kp_question_type`/`t_kp_question_type_alias`（题型→知识点域）保留不动、独立存在——一个环节故障不影响另一个。
- **聚合改按钮手动触发，不做定时任务**：移除 `KpBatchScheduler` 定时（3:17 聚合 / 3:37 维护），保留 `POST /aggregation/run` 手动按钮；批量聚集同样手动触发（面试项目不引入 @Scheduled）。
- **域 B 独立化（题型↔知识点 = 查表只读 + 独立维护，去自动关联）**：所有入口（analyze-question / 答疑）识别到**题型**即停，不再自动往下关联知识点——查题型库命中返回权威分布、未命中返回「仅题型+canonical」（空知识点，不挂起/不写 obs/不顺带 LLM kps）。题型↔知识点关联由**独立逻辑**（ADMIN 维护接口手动配）维护，入口只读——替代「obs 共现 → LLM 归纳 → 分布桶」的自动涌现链路（聚合/挂起/澄清批处理本期停用）。业务不成熟期不自动关联，可演示、可解释、可控。

## Capabilities

### New Capabilities

- `question-mastery-pipeline`: 题目全量采集 → 掌握信号（直接答对/引导后答对/答错 + 打折）→ 累计平均聚合 → `getMastery` 连续百分比 + 按题型查题目。掌握度数据底盘。
- `topic-label-normalization`: 题型名落库前归一——字符级规则 + 向量库最近邻 → canonical；掌握表 key 源头归一不裂行。

### Modified Capabilities

<!-- 后端现有 specs 为 kg/org 域，学习域无既有 spec，本期无 delta spec -->

## Impact

- **新表**：`t_student_question_record`（题目 + 信号 + 引导轮数 + canonical 归属 + `session_id` 原题链接）；`t_student_topic_mastery` 改造（`mastery_level` 语义从置信度改正确率累计、加 `source`/`train_count`）。
- **新基础设施**：Python 向量服务端点（dashscope embedding + CosVectorsClient，COS Vector Bucket 存储）+ Java HTTP 桥；**后续 RAG 复用同一套向量基础设施**。
- **改写**：`applyMasteryAndErrors`（max 单调 → 累计平均 + 题目落库）、`getStudentMastery`（连续百分比 + source + trainCount）。
- **新增端点**：按题型查题目列表 `GET /students/{id}/topics/{topicLabel}/questions`。
- **契约**：`GET /students/{id}/mastery` 响应变更（BREAKING，前端联调）。
- **依赖**：dashscope text-embedding-v3（Python gateway 复用，成本已确认）+ 阈值 spike。
- **域 B 独立化**：analyze/答疑入口停写「题型→知识点」obs、停用挂起/澄清/聚合自动关联；新增 ADMIN 维护接口（题型↔知识点手动配，查表只读）；`getMastery` PENDING 语义改「题目 canonical 未归属」（不再 obs）。
- **Python 改动范围**：仅**新增**向量服务端点（decide/信号链路仍零改动；COS 无 Java SDK，向量走 Python 桥）。
