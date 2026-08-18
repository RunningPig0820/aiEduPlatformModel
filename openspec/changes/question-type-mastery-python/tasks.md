# question-type-mastery-python 实施任务

> **范围**：Python 新增 2 个向量端点（dashscope embedding + CosVectorsClient），支撑后端题型动态聚集。`vector_type` 必填路由到多索引，本期唯一合法值 `"topic"`；`question`/`rag` 索引为配置占位。decide/generate/question-understand 零改动。
>
> **前置**：spike（任务 1）收口 CosVectorsClient 签名 + 建索引 + 近邻命中率，再进任务 2~5。

## 1. 技术预演（spike，前置）

- [x] 1.1 确认 COS 向量桶开通信息：region、bucket 名、index 名；Python 侧装 `cos-python-sdk-v5`
- [x] 1.2 控制台建 `topic-index`（768 维 cosine）——或 SDK `create_index`（API 名 spike 确认）
- [x] 1.3 `CosVectorsClient` 初始化 + `put_vectors`/`query_vectors` 签名验证（官方 Python 示例跑通）
- [x] 1.4 维度验证：dashscope `text-embedding-v3` **显式 `dimensions=768`**，确认输出维度与索引一致
- [x] 1.5 近邻验证：造 10 条近义/变体题型名（鸡兔同笼/鸡兔同笼问题/假设法）入库 → 查 top-1 验证命中 + distance 语义
- [x] 1.6 子账号密钥向量桶权限验证（桶策略授权）— 授权 `QcloudCOSFullAccess` 后 get/put/query/delete 全程 OK
- [x] 1.7 **✅ 完成标准**：CosVectorsClient 入库/查询 OK + 768 维对齐 + 近邻命中验证；Open Questions 收口（签名/建索引方式/distance 字段名）

## 2. 配置 + 依赖

- [x] 2.1 `requirements.txt` + `cos-python-sdk-v5`
- [x] 2.2 `config/settings.py` + `COS_VECTORS_SECRET_ID/KEY/REGION/BUCKET/INDEXES`（路由表默认 `{"topic": "topic-index"}`，question/rag 注释占位）
- [x] 2.3 `.env.example` + COS 配置注释（复用 `DASHSCOPE_API_KEY`，不新增）
- [x] 2.4 `.env` 填真实值（需要用户提供，见交付物）— 已在 spike 期间写入并验证 settings 可加载

## 3. 核心模块

- [x] 3.1 `models/vector.py`：`VectorPutRequest`（key/text/**vector_type 必填**/metadata）、`VectorQueryRequest`（text/top_k/**vector_type 必填**）、`VectorHit`、`VectorPutResponse`、`VectorQueryResponse`
- [x] 3.2 `core/tutoring/vector_store.py`：`embed(text)` → dashscope embeddings（`text-embedding-v3`，`dimensions=768` 常量）
- [x] 3.3 `vector_store.py`：`_resolve_index(vector_type)` 路由表，未知 → ValueError → 400
- [x] 3.4 `vector_store.py`：`put_vector`（embed → `put_vectors(Bucket, Index, [{key, data, metadata}])`，key 相同 upsert）
- [x] 3.5 `vector_store.py`：`query_vector`（embed → `query_vectors(.., ReturnMetadata=True, ReturnDistance=True)` → hits）
- [x] 3.6 `CosVectorsClient` 单例懒加载（`COS_VECTORS_*` 配齐才初始化）；embedding 失败与 COS 失败日志分开 tag

## 4. 端点

- [x] 4.1 `api/vector.py`：`POST /api/tutoring/vector/put`（`verify_internal_token`，同步 JSON 返回）
- [x] 4.2 `api/vector.py`：`POST /api/tutoring/vector/query`（同上）
- [x] 4.3 `main.py` 注册 vector router

## 5. 测试

- [x] 5.1 单测（mock embedding + mock CosVectorsClient）：put 正常 / key 覆盖 / query 返回 hits 排序 / 无近邻空数组 / 未知 vector_type → 400 / 缺 vector_type → 422 / 缺 token → 403 / embedding 失败 → 500 / COS 失败 → 500
- [x] 5.2 索引路由单测：vector_type → 物理索引映射正确；question/rag 占位不参与路由
- [ ] 5.3 契约联调：Java 桥 put → query 近邻命中（真实 COS 桶 + 真实 dashscope）
  > ⛔ 阻塞：跨仓库，需 Java `TopicVectorStore` 接线（后端 question-type-mastery-backend 任务 2.3）+ 真实桶/密钥。Python 侧端点已就绪。

- [ ] **✅ 完成标准**：端点可用（单测绿 + 联调近邻命中），decide/generate/question-understand 回归零改动
