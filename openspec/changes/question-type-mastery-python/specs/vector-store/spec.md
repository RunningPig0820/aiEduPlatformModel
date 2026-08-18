# vector-store 能力规格

Python 向量服务端点：dashscope embedding + COS 向量桶（CosVectorsClient）put/query，`vector_type` 索引路由。支撑后端题型动态聚集，后续 RAG 复用同一套端点。

## ADDED Requirements

### Requirement: 向量写入 put

`POST /api/tutoring/vector/put` SHALL 接收「文本 + key + 必填 vector_type + metadata」，用 dashscope `text-embedding-v3`（768 维）embedding 后经 `CosVectorsClient.put_vectors` 写入对应索引。key 相同 SHALL upsert 覆盖。

#### Scenario: 正常写入
- **WHEN** 请求携带 `{key, text, vector_type, metadata}`
- **THEN** 返回 `{ok: true, key}`，向量已写入 `vector_type` 对应索引

#### Scenario: key 相同覆盖
- **WHEN** 同一 `vector_type` 下再次写入相同 key
- **THEN** 旧向量被覆盖，不产生重复记录

### Requirement: 向量查询 query

`POST /api/tutoring/vector/query` SHALL 接收「文本 + top_k + 必填 vector_type」，embedding 后经 `CosVectorsClient.query_vectors` 查对应索引最近邻 Top-K，返回 hits（key/metadata/distance，**distance 越小越相似**）。

#### Scenario: 正常查询
- **WHEN** 请求携带 `{text, top_k, vector_type}`
- **THEN** 返回 `{hits: [{key, metadata, distance}]}`，hits 按 distance 升序，最多 top_k 条

#### Scenario: 无近邻
- **WHEN** 查询文本在索引中无相似向量
- **THEN** 返回空 hits 数组（HTTP 200，不视为错误）

### Requirement: vector_type 索引路由

`vector_type` SHALL 为 put/query 请求的**必填字段**（无缺省、无跨索引查询），Python 经配置映射表 `COS_VECTORS_INDEXES` 路由到物理索引。本期唯一合法值 `"topic"`；`question`/`rag` 为配置占位（不建索引）。

#### Scenario: 合法 vector_type
- **WHEN** 请求携带映射表中存在的 `vector_type`（本期 `"topic"`）
- **THEN** 向量写入/查询落到对应索引

#### Scenario: 未知 vector_type
- **WHEN** 请求携带映射表中不存在的 `vector_type`
- **THEN** 返回 HTTP 400（Java 桥据此降级回退字符规则）

#### Scenario: 缺省不兜底
- **WHEN** 请求未携带 `vector_type`
- **THEN** 返回 HTTP 422 参数校验错误（不猜测默认索引）

### Requirement: 内部鉴权

两个端点 SHALL 与 tutoring 端点家族一致，要求 `x-internal-token` 头与 `settings.INTERNAL_TOKEN` 匹配，否则返回 403。

#### Scenario: 有效 token
- **WHEN** 请求携带正确 `x-internal-token`
- **THEN** 端点正常处理

#### Scenario: 缺失/错误 token
- **WHEN** 未携带或携带错误 `x-internal-token`
- **THEN** 返回 403

### Requirement: 失败语义（错误冒泡）

端点异常（embedding 调用失败 / COS 读写失败 / 建索引缺失）SHALL 返回 HTTP 5xx 错误码并记录日志，**不吞异常、不返回降级空结果**——Java 桥侧据此回退字符规则 + 原样落库，不阻塞主链路。

#### Scenario: embedding 失败
- **WHEN** dashscope embedding 调用失败
- **THEN** put/query 返回 HTTP 500，Java 桥降级，主链路不阻塞

#### Scenario: COS 读写失败
- **WHEN** CosVectorsClient 写入/查询失败
- **THEN** 返回 HTTP 500，Java 桥降级，主链路不阻塞
