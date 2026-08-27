# 背景：现有能力与缺口

> summary: 题型分析后端：analyze-question 无独立 REST（resolve 是 label 级），题型库逐字聚类裂行稀释，需建题目→题型→知识点独立链路。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-Context.md
> 类别：项目介绍

---

### 背景：现有能力与缺口

> 检索摘要：题型分析后端：analyze-question 无独立 REST（resolve 是 label 级），题型库逐字聚类裂行稀释，需建题目→题型→知识点独立链路。

- **现有能力**：`POST /api/kp/resolve`（题型名 label → TextbookKP URI，管线 ①镜像 → ②题型库年级匹配 → ③LLM 消歧 → ④PENDING，写 obs）、`POST /api/kp/vote`（学生确认落 STUDENT_VOTE 观测）、题型库聚合任务（凌晨扫 obs 建 CANDIDATE + LLM 归纳 ratio）、题型库分页 + 关联知识点接口。全部已收口（`kp-matching-lightup`）。
- **缺口**：`resolve` 是 **label 级**，需先知道题型名；「题目文本 → 题型名」的题目理解只在答疑 Python `decide` 会话内（SSE 绑定），无独立 REST。
- **题型库健康问题**：聚合按 `topic_label` **逐字聚类**（`groupingBy(getTopicLabel)`），相似题型叫法不一（「鸡兔同笼」vs「鸡兔同笼问题」）裂成重复条目、聚合阈值（≥3 学生/≥5 命中）被劈开稀释；学生确认 vote 的 topicLabel 也会落成重复题型。
- **前提**：无现成完整知识点/题库标注表；知识点用 TextbookKP URI 锚定（kg-sync 镜像），题型名 ≠ 知识点名，靠 LLM 翻译 + 镜像校验 + 观测共现桥接。

**已拍板（用户）**：题目理解 Java 自研（端口预留，可后续换 Python 独立端点）；本期范围 = 核心两件（analyze-question 端点 + 题型库别名合并），Q3 跨来源观测、Q4 批量扫题库为后续阶段。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§背景：现有能力与缺口）｜ 完善文档 01-模块定位与核心价值.md
