# 粗筛机制设计（采纳 DeepSeek 建议）

> summary: 原方案遍历5000+图谱知识点致LLM调用量爆炸，改为两阶段：教材知识点先粗筛top-20候选再LLM投票，对比difflib与向量检索方案。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D4-2-粗筛机制设计.md
> 类别：数据关联

---

### D4.2：粗筛机制设计（采纳 DeepSeek 建议）

> 检索摘要：原方案遍历5000+图谱知识点致LLM调用量爆炸，改为两阶段：教材知识点先粗筛top-20候选再LLM投票，对比difflib与向量检索方案。

**问题**: 原方案遍历所有图谱知识点（5000+），LLM调用量爆炸

**解决方案**: 两阶段匹配

```
教材知识点 → 粗筛(top-20候选) → LLM双模型投票 → 匹配结果
```

**粗筛方式对比**:

| 方案 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| **difflib** (原方案) | 字符相似度匹配 | 无依赖、速度快 | 语义理解弱 |
| **向量检索** (新方案) | Embedding语义匹配 | 自动理解同义词、语义强 | 需安装依赖 |

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D4.2：粗筛机制设计（采纳 DeepSeek 建议））
