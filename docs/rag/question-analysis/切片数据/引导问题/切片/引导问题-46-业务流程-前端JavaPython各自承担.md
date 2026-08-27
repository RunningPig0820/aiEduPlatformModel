# 前端 / Java / Python 在业务闭环里各自承担什么？

> summary: 前端 / Java / Python 在业务闭环里各自承担什么？
> 权威度: 1.0
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/引导问题/引导问题-46-业务流程-前端JavaPython各自承担.md
> 类别：业务流程

---

## 回答

**核心结论**：**前端**负责触发 + 展示（贴题/拍题/掌握度页）；**Java** 负责编排 + 决策 + 落库（学科门编排、canonical 归并、掌握度计算、防作弊护栏、两表落库）；**Python** 是纯智能无状态桥（学科门判定、图片题型识别、decide 信号、向量原语）——落库/映射/决策全在 Java，Python 不落任何业务库。

**分层展开**：
- **前端**：`AiQa.jsx` 答疑对话 / 题型分析页贴题拍题 / 掌握度页展示——只触发和渲染，不碰决策。（依据：分析-02）
- **Java**：`TutoringAppService` 编排全链路 + `TopicLabelAggregationService` canonical 归并 + `ScoreMapper` 掌握度计算 + 防作弊护栏 + 题目表/掌握表/Redis 会话落库——**平台决策层**。（依据：分析-02 / 分析-05）
- **Python**：`api/tutoring.py` 四端点（subject-classify / question-understand / decide / generate）+ `api/vector.py` put/query——纯智能桥，无状态不落库，显式禁止做题型↔知识点映射。（依据：分析-02）
- **失败语义分工**：业务判定（学科门/识别）吞异常降级空；向量基础设施错误冒泡让 Java 感知后降级——分工决定谁的故障影响谁。（依据：分析-02 / 分析-10）

> 证据：详见 `7. 引导问题/问题列表.md`（第 46 问）｜ `4.完善文档/03-架构与微服务分工.md` ｜ `3.代码/分析-02-微服务分工.md`
