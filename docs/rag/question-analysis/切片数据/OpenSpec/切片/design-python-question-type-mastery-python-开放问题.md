# 开放问题（spike 已收口）

> summary: spike 已收口：CosVectorsClient 签名/控制台建索引/距离语义/子账号权限均已验证。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-question-type-mastery-python-开放问题.md
> 类别：未来演进

---

### 开放问题（spike 已收口）

> 检索摘要：spike 已收口：CosVectorsClient 签名/控制台建索引/距离语义/子账号权限均已验证。

- ✅ **`CosVectorsClient` 签名**：`CosConfig(Region, SecretId, SecretKey)` → `CosVectorsClient(config)`；`put_vectors(Bucket, Index, Vectors)` / `query_vectors(Bucket, Index, QueryVector, TopK, Filter, ReturnDistance, ReturnMetaData, ...)` 返回 `(resp, data)`，命中在 `data["vectors"]`。
- ✅ **建索引**：控制台已建 `topic-index`（`get_index` 实测 `dataType=float32, dimension=768, distanceMetric=cosine`）；SDK 另有 `create_index(Bucket, Index, DataType, Dimension, DistanceMetric, ...)` 可作备选。
- ✅ **distance 语义**：`distanceMetric="cosine"`，**distance 越小越相似，self 命中 ≈ 0**。实测示例：鸡兔同笼→鸡兔同笼问题 0.077 / 笼中鸡兔 0.096；一元二次方程求解→解一元二次方程 0.026 / 一元二次方程 0.061；行程问题→相遇问题 **0.332 边界**、异型（鸡兔同笼）0.481——**同型与异型在 ~0.3~0.48 之间有清晰间距，阈值区间可用**。
- ✅ **子账号密钥权限**：需授权（附 `QcloudCOSFullAccess` 后 get/put/query/delete 全通）。

> 证据：详见 `2.OpenSpec design 决策/design-python-question-type-mastery-python.md`（§开放问题）
