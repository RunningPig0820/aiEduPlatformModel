# design-python-ai-tutoring-question-understand

> summary: 面试问答中AI辅导题理解的命名收敛机制
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D4. 命名收敛（topicHint 注入）—— 词汇桥关键机制
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring-question-understand
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-ai-tutoring-question-understand-D4-命名收敛topicHint-注入-词汇桥关键机制.md
> 类别：架构设计

---

### D4. 命名收敛（topicHint 注入）—— 词汇桥关键机制

Java 侧调用时把 `findTopTopicLabels(20)`（题型库 top-N，Java 数据库）放 `topicHint` 传入；prompt 写「优先从参考词表选取题型名，词汇不足可自拟」。让 Python 图片识别命名朝题型库收敛，与 Java 文本识别（KpQuestionAnalyzer，D1 词表注入）对齐 —— 同一 resolve 管线合并，别名合并兜底。这是两端题目理解词汇一致性的唯一机制，**必须让 Java 配合传 topicHint**。
