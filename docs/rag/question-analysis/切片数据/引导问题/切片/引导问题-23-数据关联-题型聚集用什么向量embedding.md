# 题型动态聚集用什么向量？embedding 用哪个模型、多少维？

> summary: 题型动态聚集用什么向量？embedding 用哪个模型、多少维？
> 权威度: 1.0
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/引导问题/引导问题-23-数据关联-题型聚集用什么向量embedding.md
> 类别：数据关联

---

## 回答

**核心结论**：题型动态聚集用**题型名向量**（单信号），embedding 用 dashscope **text-embedding-v3**、显式 **768 维**（默认 1024，必须与索引一致），存 COS 向量桶 `topic-index`（768 维 cosine）。

**分层展开**：
- **聚集依据 = 题型名向量单信号**：字符规则先拦确定性变体（解X/求X前缀 + 全半角/标点归一），题型名向量处理语义同型（鸡兔同笼/鸡兔同笼问题/假设法）；**题目向量本期不落库**。（依据：完善文档 06 / 分析-06）
- **embedding 模型**：dashscope `text-embedding-v3`（OpenAI 兼容端点），复用现有 dashscope 配置不进 LLMFactory。（依据：完善文档 03 / 分析-06）
- **维度坑**：**必须显式 `dimensions=768`**——模型默认输出 1024 维，与 768 维索引对不上；**索引维度建好后不可改**，所以 spike 第一步就是验证显式 768 的实际输出。（依据：坑档案 J-QT4 / 分析-06）
- **索引路由**：`vector_type="topic"` 必填 → 路由 topic-index（768 维 cosine）；`question`/`rag` 纯配置占位。（依据：完善文档 03 / 分析-06）

> 证据：详见 `7. 引导问题/问题列表.md`（第 23 问）｜ `4.完善文档/06-题型动态聚集与向量.md` ｜ `5.难点/坑档案.md`（J-QT4）
