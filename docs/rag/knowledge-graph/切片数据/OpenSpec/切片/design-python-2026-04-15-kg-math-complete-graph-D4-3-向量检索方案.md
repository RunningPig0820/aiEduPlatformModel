# 向量检索方案（推荐采用）

> summary: 推荐用BAAI/bge-small-zh-v1.5做Embedding语义检索，numpy暴力搜索top-20候选，内存约3.5GB，预计匹配准确率提升10-20%。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D4-3-向量检索方案.md
> 类别：数据关联

---

### D4.3：向量检索方案（推荐采用）

> 检索摘要：推荐用BAAI/bge-small-zh-v1.5做Embedding语义检索，numpy暴力搜索top-20候选，内存约3.5GB，预计匹配准确率提升10-20%。

**核心思想**: 将知识点转换为语义向量，通过余弦相似度找到语义最接近的候选

```python
class LocalVectorRetriever:
    """本地向量检索器"""

    def __init__(self, kg_concepts):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
        self.texts = [f"{c['label']} {c.get('description','')}" for c in kg_concepts]
        self.vectors = self.model.encode(self.texts, show_progress_bar=True)
        self.concepts = kg_concepts

    def retrieve(self, query: str, top_k=20):
        q_vec = self.model.encode([query])[0]
        scores = np.dot(self.vectors, q_vec) / (np.linalg.norm(self.vectors, axis=1) * np.linalg.norm(q_vec))
        top_idx = np.argsort(scores)[-top_k:][::-1]
        return [self.concepts[i] for i in top_idx]
```

**技术选型**:

| 组件 | 选择 | 理由 |
|------|------|------|
| Embedding 模型 | `BAAI/bge-small-zh-v1.5` | 中文小模型 SOTA，内存 2-4GB，维度 512 |
| 向量索引 | `numpy` 暴力搜索 | 图谱 ≤ 5000 条，暴力计算足够快（< 10ms） |
| 依赖库 | `sentence-transformers` | 一行代码加载模型，自动处理 tokenization |

**资源评估**:

| 项目 | 数值 | 说明 |
|------|------|------|
| 模型内存 | 2.5 GB | bge-small-zh-v1.5 实际占用 |
| 向量存储 | 5000 × 512 × 4字节 ≈ 10 MB | numpy float32 |
| 其他开销 | < 1 GB | 原有数据结构 |
| **总计** | **约 3.5 GB** | 远低于 8GB 限制 |

**预期收益**:

| 指标 | 改进前 (difflib) | 改进后 (向量) |
|------|------------------|---------------|
| 候选语义相关性 | 低（仅字符匹配） | 高（理解同义词、语序） |
| 漏匹配风险 | 中（"勾股定理" vs "毕达哥拉斯定理"） | 极低 |
| LLM 调用次数 | 不变（仍为 top-20） | 不变 |
| 总体匹配准确率 | 基准 | **预计提升 10-20%** |

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D4.3：向量检索方案（推荐采用））
