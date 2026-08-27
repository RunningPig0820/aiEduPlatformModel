# 目标与非目标

> summary: 目标=put/query 向量端点+vector_type 必填路由+embedding 复用 dashscope+错误冒泡；非目标=相似题/rag 索引/批处理/改既有链路。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-question-type-mastery-python-Goals-Non-Goals.md
> 类别：项目介绍

---

### 目标与非目标

> 检索摘要：目标=put/query 向量端点+vector_type 必填路由+embedding 复用 dashscope+错误冒泡；非目标=相似题/rag 索引/批处理/改既有链路。

**Goals:**
- 新增 2 个向量端点（put/query），支撑后端题型动态聚集。
- 多索引 + `vector_type` 必填路由：本期 `topic`，`question`/`rag` 配置占位，后续加索引 Python 零代码改动（RAG 铺路）。
- embedding 复用 dashscope（`DASHSCOPE_API_KEY` + 现成 base URL），不引入新密钥。
- 错误冒泡给 Java 桥降级，不阻塞主链路。

**Non-Goals:**
- **不做相似题存储/检索**：本期不落题目向量、不建 `question` 索引（仅配置占位）。
- 不建 `rag` 索引（占位）。
- 不做批处理/定时任务（后端已定手动触发）。
- 不改 decide / generate / question-understand 及既有 gateway。

> 证据：详见 `2.OpenSpec design 决策/design-python-question-type-mastery-python.md`（§目标与非目标）
