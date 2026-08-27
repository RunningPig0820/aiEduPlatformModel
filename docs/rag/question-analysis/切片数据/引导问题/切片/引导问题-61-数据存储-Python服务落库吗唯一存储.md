# Python 服务落库吗？Python 唯一的"存储"是什么？

> summary: Python 服务落库吗？Python 唯一的"存储"是什么？
> 权威度: 1.0
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/引导问题/引导问题-61-数据存储-Python服务落库吗唯一存储.md
> 类别：数据存储

---

## 回答

**核心结论**：Python **不落任何业务库**（无 ORM/MySQL/Redis 依赖），唯一"存储" = **COS 向量桶**（题型名向量，metadata 透传不落库）——Python 是纯智能无状态桥，数据全在 Java。

**分层展开**：
- **不落业务库**：Python 无 ORM/MySQL/Redis 依赖，题目由 history 推断（Java 零题目状态）；落库/映射/决策全在 Java。（依据：分析-07 / 分析-02）
- **唯一存储 = COS 向量桶**：`put_vectors`/`query_vectors` 存题型名向量（768 维），metadata 透传不落库——别误以为 Python 把题目/掌握度存了库。（依据：分析-07 / 完善文档 05 存储拓扑）
- **为什么这样**：纯智能无状态 → 可水平扩展、任何一轮可被新机器接管；数据职责收敛在 Java，Python 只做 LLM + 向量原语。（依据：分析-02 设计要点）
- **状态与数据分离**：Python stateless（纯智能），Java 管状态（Redis/session）与数据（两表）。（依据：分析-07 设计要点）

> 证据：详见 `7. 引导问题/问题列表.md`（第 61 问）｜ `4.完善文档/05-数据落库与掌握度.md` ｜ `3.代码/分析-07-数据流与存储.md`
