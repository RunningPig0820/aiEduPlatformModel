# 题目理解端口抽象

> summary: 题目理解端口抽象，Java LLM 默认实现，prompt 注入题型库收词约束命名降变体漂移，预留 Python 端点可替换。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D1-题目理解端口抽象.md
> 类别：架构设计

---

### D1：题目理解端口抽象，Java LLM 默认实现（题型名 → 空挂库锚）

> 检索摘要：题目理解端口抽象，Java LLM 默认实现，prompt 注入题型库收词约束命名降变体漂移，预留 Python 端点可替换。

新增 domain 端口 `QuestionUnderstandingPort`：

```java
/** 题目文本 → 候选题型名（LLM 题目理解）。纯识别，不查库不落库。 */
List<String> understand(String questionText, Integer grade);
```

默认实现 `KpQuestionAnalyzer`（infra，`@Component`）：复用 `LlmGateway.chat()` + 新 prompt「识别这道数学题的题型名，每行一个，限 1~5 个，不要编号/解释」，解析复用 `KpLlmDisambiguator.parseNames` 的去编号/bullet 逻辑。

**关键：prompt 注入题型库已收词**——把当前题型库 top-N 常用题型名（`QuestionTypeRepository.findTopTopicLabels(20)`）作为「参考题型词表」带进 prompt（"优先从参考词表选取，词汇不足可自拟"）。让 LLM 的题型命名**偏向现有词汇**，从源头降低变体漂移（这是别名合并之外的第一道防线，纯 prompt 零成本）。LLM 失败 → 返回空列表，analyze-question 降级 PENDING。

**为什么 Java 而非 Python**（用户已拍板）：自包含、不阻塞跨仓库；词汇分歧由 D3 别名合并 + prompt 词表兜底。端口抽象保留 Python 独立端点（拆 decide 题目理解）为后续可替换实现——换实现只动 infra 装配，不动 domain/application。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D1）｜ 语雀-决策记录.md D20 ｜ 完善文档 03-架构与微服务分工.md
