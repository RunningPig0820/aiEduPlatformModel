# /api/tutoring/vector 接口文档（Java↔Python 桥）

> Java 内部通道（`x-internal-token`），供后端 `TopicVectorStore` 端口调用。
> 字段沿用 tutoring 端点家族约定（**snake_case**，与 decide/generate/question-understand 一致）。
>
> **`vector_type` 必填**：每次 put/query 由 Java 显式确定索引，本期唯一合法值 `"topic"`（题型名向量）。

## 1. 存向量 put

`POST /api/tutoring/vector/put`

```json
{
  "key": "q_5001",
  "text": "鸡兔同笼",
  "vector_type": "topic",
  "metadata": {
    "student_id": "1001",
    "topic_label": "鸡兔同笼",
    "canonical_label": "鸡兔同笼",
    "timestamp": "2026-08-18T10:00:00"
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| key | String | 是 | 向量业务 ID（key 相同覆盖 upsert） |
| text | String | 是 | 要向量化的文本（本期为题型名；题目文本不落库） |
| vector_type | String | 是 | 索引路由键，本期唯一合法值 `"topic"` |
| metadata | Object | 否 | 透传存进向量桶（student_id/topic_label/canonical_label/timestamp），Python 不改写 |

**响应**

```json
{ "ok": true, "key": "q_5001" }
```

## 2. 查最近邻 query

`POST /api/tutoring/vector/query`

```json
{
  "text": "鸡兔同笼问题",
  "top_k": 3,
  "vector_type": "topic"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | String | 是 | 要向量化的查询文本 |
| top_k | Integer | 是 | 返回最近邻条数 |
| vector_type | String | 是 | 查询哪个索引，本期唯一合法值 `"topic"` |

**响应**

```json
{
  "vectors": [
    {
      "key": "q_5001",
      "metadata": { "topic_label": "鸡兔同笼", "canonical_label": "鸡兔同笼" },
      "distance": 0.12
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| vectors | Array | 最近邻列表（对齐 COS `query_vectors` 返回字段名），按 distance 升序；**无近邻返回空数组（HTTP 200，不是错误）** |
| vectors[].key | String | 向量 key |
| vectors[].metadata | Object | 该向量存入时的 metadata |
| vectors[].distance | Float | 余弦距离，**越小越相似**（self 命中 ≈ 0） |

> ⚠️ **写入延迟**：put 后索引异步生效，约 **~10s 后才可被 query 命中**。Java 桥「put 后立即 query」路径需留延迟或容忍首查 miss。

## 3. 错误

| 场景 | HTTP | 说明 |
|------|------|------|
| 缺失/错误 `x-internal-token` | 403 | 内部鉴权失败 |
| 缺 `vector_type`（必填校验） | 422 | Pydantic 必填字段缺失 |
| 未知 `vector_type`（不在索引映射表） | 400 | Java 桥降级回退字符规则 |
| embedding 失败（dashscope） | 500 | Java 桥降级回退字符规则 |
| COS 读写失败 | 500 | Java 桥降级回退字符规则 |

## 4. 调用方（Java）约定

1. `TopicVectorStore.putVector(key, text, metadata)` → 调 put，`vector_type="topic"`。
2. `TopicVectorStore.queryNearestTop1(text)` → 调 query（top_k 按后端聚集逻辑定），取 hits[0]。
3. 任一错误 → Java 降级：回退字符规则 + 原样落库，**不阻塞主链路**（后端 design 风险项）。
4. **Java 不碰 embedding API / COS SDK**——只在 metadata 里传业务字段。
