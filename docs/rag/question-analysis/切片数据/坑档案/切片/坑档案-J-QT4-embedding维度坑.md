# 坑档案 J-QT4 embedding 维度坑：默认 1024 与索引对不上

> summary: embedding 维度坑：默认 1024 与索引对不上
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J-QT4. embedding 维度坑
> 模块: question-analysis ｜ 节: 坑档案
> COS路径: rag-slices/question-analysis/坑档案/坑档案-J-QT4-embedding维度坑.md
> 类别：开发难点

---

**1. 问题现象**：写入索引的向量维度与索引声明维度不一致，查询报错或结果为空。

**2. 触发流程**：`text-embedding-v3` 不显式 `dimensions` → 输出 1024 维 → 写进 768 维索引。

**3. 根因分析**：dashscope `text-embedding-v3` **默认输出 1024 维**，合法维度 1024/768/512…，不显式指定就 1024，与建的 768 维索引对不上。**索引维度建好后不可改**。

**4. 排查过程**：spike 第一步验证 `dimensions=768` 实际输出 768 维。

**5. 解决方案 & 改动点**：**`dimensions=768` 写死常量**；spike 顺序必须是"先验证维度 → 再建索引"，不可颠倒。（`core/tutoring/vector_store.py:26-28`）

**6. 面试口述要点**：embedding 的维度必须和索引维度严格一致，这是建索引前就要钉死的。text-embedding-v3 默认输出 1024 维，不显式传 768 就和索引对不上，而且索引建好后改不了。所以 spike 第一步就是验证显式 768 的实际输出。
