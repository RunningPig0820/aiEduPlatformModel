# D3：vector_store.py 唯一核心模块

> summary: vector_store.py 唯一核心模块封装 put/query，CosVectorsClient 单例懒加载，写入 ~10s 异步生效、返回结构按 COS 实测对齐。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-question-type-mastery-python-D3-vector_store.py-唯一核心模块.md
> 类别：架构设计

---

### D3：`vector_store.py` = 唯一核心模块

> 检索摘要：vector_store.py 唯一核心模块封装 put/query，CosVectorsClient 单例懒加载，写入 ~10s 异步生效、返回结构按 COS 实测对齐。

```
core/tutoring/vector_store.py
  embed(text) -> List[float]                     # dashscope embedding, 768 维
  put_vector(key, text, vector_type, metadata)   # embed → put_vectors(Bucket, index, [..])
  query_vector(text, top_k, vector_type)         # embed → query_vectors(..) → hits
  _resolve_index(vector_type)                    # 路由表; 未知 → 抛 ValueError → 400
```

- `CosVectorsClient` 单例懒加载（`COS_VECTORS_*` 配齐才初始化）。
- put：`put_vectors(Bucket, Index, [{key, data:{float32}, metadata}])`，key 相同 upsert。**实测返回 header dict（无 body 引用），`resp.status` 为 None 是正常的**（成功看是否有异常抛出）。
- query：**实测签名 `query_vectors(Bucket, Index, QueryVector, TopK, Filter=None, ReturnDistance=None, ReturnMetaData=None, **kwargs)`**——注意是 **`ReturnMetaData`（大写 M）**；返回 **`(resp, data)` 元组**，命中在 `data["vectors"]`（每项 `{key, metadata, distance}`），**不是契约里的 `hits`**。
- **写入延迟（实测关键）**：`put_vectors` 后索引**异步生效，约需等待 ~10s 才可查询到**（立即 query 返回空 `vectors: []`）。后端 Java 桥在「首题建锚后立查」路径要留意——建议 put 与 query 之间留延迟，或首题建锚后不立即 query（本身无近邻）。
- **metadata 透传**：Java 传什么存什么（student_id/topic_label/canonical_label/timestamp），Python 不解释、不改写。

> 证据：详见 `2.OpenSpec design 决策/design-python-question-type-mastery-python.md`（§D3）｜ 完善文档 06-题型动态聚集与向量.md ｜ 坑档案 J-QT1
