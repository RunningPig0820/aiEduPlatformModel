# 独立 analyze-question 端点

> summary: 单题分析=独立 analyze-question 端点（从 decide 拆出题目理解），无状态一次性请求，多入口复用。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-kp-question-analysis-D1-独立analyze-question端点.md
> 类别：架构设计

---

### 决策 1：单题分析 = 独立 `analyze-question` 端点（从 decide 拆出「题目理解」，非整个 decide）

> 检索摘要：单题分析=独立 analyze-question 端点（从 decide 拆出题目理解），无状态一次性请求，多入口复用。

新增 `POST /api/kp/analyze-question { text }`，响应 `{ topicLabel, status, confidence, knowledgePoints: [{kpUri, kpLabel, gradeRange, ratio}] }`（PENDING 时 knowledgePoints 空 + candidates）。

理由：单题分析是**无状态一次性请求**（贴题→结果），答疑是**多轮 SSE 会话**，交互模型不同，不该绑会话。独立端点 = 独立「题目→题型/知识点」能力，答疑/练习/题型分析多入口复用。实现复用 resolve 管线的题型识别（镜像 → 题型库 → LLM 消歧），把「题目理解」从 Python decide 拆出为独立调用，而非复用整个 decide 流程（decide 还含引导策略/护栏）。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-question-analysis.md`（§决策 1）｜ 语雀-决策记录.md D20/D21 ｜ 完善文档 03-架构与微服务分工.md
