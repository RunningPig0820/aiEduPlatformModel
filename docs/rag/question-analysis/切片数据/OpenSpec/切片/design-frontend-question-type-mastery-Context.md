# 背景

> summary: 掌握度=题型已确立但数据底盘零散（无题目记录/题型名不收敛/算不出可追溯百分比），需建可追溯掌握度页。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-question-type-mastery-Context.md
> 类别：项目介绍

---

### 背景：掌握度 = 题型，数据底盘零散

> 检索摘要：掌握度=题型已确立但数据底盘零散（无题目记录/题型名不收敛/算不出可追溯百分比），需建可追溯掌握度页。

- **现状**：掌握度 = 题型 已确立（`kp-matching-lightup` 翻转）。但数据底盘是零散观测——AI 答疑 `decide` 顺带输出 `mastery_signals`，题型分析页 `analyze-question` 纯分析不落观测。**没有统一的题目记录、没有题型名的规范收敛、掌握度算不出可追溯的百分比。**
- **诉求**：掌握度业务含义通透——学生掌握的是**题型**（解题模式），不是知识点（教材概念）。要让学生看到「某题型 64%，练了 10 题，来源 AI/题库，可跳转看题目」。
- **现有资产**（复用）：
  - `POST /api/tutoring/ocr`（图片题识别文本）、`POST /api/kp/analyze-question`（贴题识别题型）、`POST /api/kp/resolve`（题型 label 解析候选）。
  - 腾讯 COS 已在答疑链路使用（`uploadQuestionImage` → COS → 多模态），向量化存储可复用同一 COS 账号，新增向量索引/检索能力。
  - 知识图谱（Neo4j）含教材知识点（`kpUri`/`kpLabel`）——本期仅展示，不参与派生。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-question-type-mastery.md`（§背景：掌握度 = 题型，数据底盘零散）｜ 完善文档 01-模块定位与核心价值.md ｜ 完善文档 05-数据落库与掌握度.md
