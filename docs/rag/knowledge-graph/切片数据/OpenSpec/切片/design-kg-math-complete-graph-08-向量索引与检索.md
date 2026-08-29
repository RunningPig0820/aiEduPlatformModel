# 向量索引与检索

> summary: 向量索引与检索
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-math-complete-graph-08-向量索引与检索.md
> 类别：架构设计

---

> 检索摘要：粗筛用什么向量模型？bge-small-zh 选型理由？numpy 暴力搜索够快吗？内存占用多大？对比 difflib 提升多少？

## 向量检索方案（D4.3，推荐采用）

核心思想：将知识点转换为语义向量，通过余弦相似度找到语义最接近的候选，作为知识图谱匹配的粗筛环节（top-20 候选）。

实现（LocalVectorRetriever）：

```python
class LocalVectorRetriever:
    def __init__(self, kg_concepts):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
        self.texts = [f"{c['label']} {c.get('description','')}" for c in kg_concepts]
        self.vectors = self.model.encode(self.texts, show_progress_bar=True)
        self.concepts = kg_concepts
    def retrieve(self, query, top_k=20):
        q_vec = self.model.encode([query])[0]
        scores = np.dot(self.vectors, q_vec) / (np.linalg.norm(self.vectors, axis=1) * np.linalg.norm(q_vec))
        top_idx = np.argsort(scores)[-top_k:][::-1]
        return [self.concepts[i] for i in top_idx]
```

技术选型：
- Embedding 模型：BAAI/bge-small-zh-v1.5，中文小模型 SOTA，内存 2-4GB，维度 512
- 向量索引：numpy 暴力搜索，图谱 ≤5000 条暴力计算足够快（<10ms）
- 依赖库：sentence-transformers，一行代码加载模型，自动处理 tokenization

资源评估：模型内存 2.5GB + 向量存储 5000×512×4字节≈10MB + 其他开销 <1GB，总计约 3.5GB，远低于 8GB 限制。

预期收益（对比 difflib）：候选语义相关性从低（仅字符匹配）到高（理解同义词、语序）；漏匹配风险从中（"勾股定理" vs "毕达哥拉斯定理"）到极低；LLM 调用次数不变（仍为 top-20）；总体匹配准确率预计提升 10-20%。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D4.3）
