# question-type-mastery-python 技术设计

## Context

- 后端方案 `question-type-mastery-backend`（Decision 5）确定：COS 向量检索无 Java SDK（只有 Python/Go 的 `CosVectorsClient`），向量操作走 Python 桥。Java 经 `TopicVectorStore` 端口 HTTP 调 Python，不碰 embedding API / COS SDK。
- 本期唯一业务用途 = **题型动态聚集**（把散题型名归一成 canonical）；**相似题检索明确不做**（后端 Non-Goal，题目向量本期不落库）。
- 现状代码事实：
  - `core/gateway/factory.py` 只创建 `BaseChatModel`（对话），**无任何 embedding 类**。
  - dashscope 已接：`factory.py:148` 用 `dashscope.aliyuncs.com/compatible-mode/v1` 走 OpenAI 兼容协议；`settings.DASHSCOPE_API_KEY` 已有（`.env.example` 已含）。→ **embedding 复用同一 base + 同一 key**。
  - `requirements.txt` 无任何 COS 依赖；`api/rag.py` 有 mock `embed` 端点（TODO，未接 main.py），不要复用。
  - `api/tutoring.py` 三端点（decide/generate SSE、question-understand 同步 JSON）统一 `x-internal-token` 鉴权 + snake_case——向量端点照此惯例。

## Goals / Non-Goals

**Goals:**
- 新增 2 个向量端点（put/query），支撑后端题型动态聚集。
- 多索引 + `vector_type` 必填路由：本期 `topic`，`question`/`rag` 配置占位，后续加索引 Python 零代码改动（RAG 铺路）。
- embedding 复用 dashscope（`DASHSCOPE_API_KEY` + 现成 base URL），不引入新密钥。
- 错误冒泡给 Java 桥降级，不阻塞主链路。

**Non-Goals:**
- **不做相似题存储/检索**：本期不落题目向量、不建 `question` 索引（仅配置占位）。
- 不建 `rag` 索引（占位）。
- 不做批处理/定时任务（后端已定手动触发）。
- 不改 decide / generate / question-understand 及既有 gateway。

## Decisions

### D1. 多索引 + vector_type 必填路由（不做单索引 filter）

后端「题目索引/题型索引/RAG 索引后面都要」——若用单索引 + metadata filter，将来切多索引要改契约。**本期就按多索引设计**：`vector_type` 是**必填**的逻辑类型，Python 经 `COS_VECTORS_INDEXES` 映射到物理索引。

```
vector_type (逻辑名)  → 物理索引 (COS)
  "topic"              →  topic-index     (本期建)
  "question"           →  question-index  (配置占位, 不建)
  "rag"                →  rag-index       (配置占位, 不建)
```

- **为什么必填而非缺省兜底**：用户拍板「每个查询由后端显式确定」。多索引下缺省语义模糊（不能跨索引全查，COS `query_vectors` 一次一个索引），必填最简单、可预期。
- **为什么映射放 Python**：Java 不感知 COS 基础设施（桥接哲学）；将来索引改名只动 Python 配置，不动 Java 契约。
- 未知 `vector_type` → 400；缺失 → 422（Pydantic 必填校验）。

### D2. embedding 复用 dashscope OpenAI 兼容端点（不塞进 LLMFactory）

`LLMFactory` 全是 `BaseChatModel`（对话），embedding 是向量编码，语义不同——**独立封装在 `vector_store.py`**，不污染既有 gateway（符合「gateway 配置不动」承诺）。

- 端点：`POST https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings`（与 `factory.py` bailian 同一 base）。
- 模型：`text-embedding-v3`，**显式 `dimensions=768`**（默认 1024，合法维度 1024/768/512/…；不显式指定则输出 1024，与索引维度对不上）。
- **选型背景（2026-08-18）**：`text-embedding-v3` 百炼**默认可用、无需开通**，直接选用不阻塞；`qwen3.7-text-embedding`（效果更好、免费额度翻倍）需开通，维度同为 768——**两者维度兼容，索引建好 768 后未来切 qwen3.7 只需换模型名，索引不重建**。
- **维度绑定约束（关键）**：索引维度必须 = embedding 输出维度，不能自由选大。put/query 两端都是同一个模型输出，维度不一致无法算相似度；**索引维度建好后不可改**。故 spike 顺序必须是「先验证 `dimensions=768` 实际输出 768 维 → 再建索引」，不可颠倒。
- **距离度量 = 余弦距离（已确认）**：文本语义检索标准，对向量长度不敏感（「鸡兔同笼」vs「鸡兔同笼的解法」语义相近余弦高）；与后端契约「768 维 cosine、distance 越小越相似」一致。排除欧氏距离（对 embedding 模长敏感，长文本被干扰）。
- 密钥：复用 `settings.DASHSCOPE_API_KEY`。
- 实现选择：`openai` SDK（requirements 已有）的 `client.embeddings.create`，或 `dashscope` SDK（已有）的 `text_embedding` 类——spike 定，优先 `dashscope` SDK（已装，官方 text-embedding-v3 示例多）。

### D3. `vector_store.py` = 唯一核心模块

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

### D4. 配置（settings.py）

```python
# ============ COS 向量桶 ============
COS_VECTORS_SECRET_ID: str = ""
COS_VECTORS_SECRET_KEY: str = ""
COS_VECTORS_REGION: str = "ap-guangzhou"
COS_VECTORS_BUCKET: str = ""                # "xxx-125xxxx"
COS_VECTORS_INDEXES: dict = {               # 逻辑类型 → 物理索引
    "topic": "topic-index",
    # "question": "question-index",         # 相似题, 预留不建
    # "rag": "rag-index",                   # RAG, 预留不建
}
```

`DASHSCOPE_API_KEY` 复用现成项，无需新增。

### D5. 失败语义 = 错误冒泡（与 question-understand 相反）

question-understand 是「绝不抛异常 → 空结果降级」（视觉识别弱，Java 有 PENDING 兜底）。**向量端点不复制此模式**：它是内部基础设施，Java 桥侧已有降级策略（回退字符规则 + 原样落库）。Python 正常抛 HTTP 错误码即可，但要**日志区分**：

- embedding 失败（dashscope）vs COS 读写失败——日志 tag 分开，便于 spike/联调定位。

## Risks / Trade-offs

- [embedding 维度坑：text-embedding-v3 默认 1024，需显式 768，且索引建好后不可改] → spike 第一步验证维度 + 建索引，`dimensions=768` 写死在常量。
- [CosVectorsClient 初始化/put/query 签名未知] → spike 前置（任务 1），官方 Python 示例跑通再写封装。
- [`query_vectors` 是否支持 metadata filter 不确定] → 多索引已规避（靠索引隔离，不靠 filter）；即使支持也不依赖。
- [建索引方式：控制台 vs SDK `create_index`] → 建议控制台建（`create_index` API 名不确定）；spike 定，两路都记。
- [子账号密钥权限不足] → 桶策略需授权向量桶操作；联调前确认（待提供参数清单）。
- [向量库冷启动（无近邻建新）] → 后端已设计首题建锚；Python 侧无感。
- [端点不可用拖慢主链路] → Java 桥 HTTP 超时短 + 降级；Python 正常错误码即可。

## Migration Plan

1. **spike（前置）**：装 `cos-python-sdk-v5`，确认 `CosVectorsClient` 初始化 + `put_vectors`/`query_vectors` 签名；控制台建 `topic-index`（768 维 cosine）；`text-embedding-v3` 显式 768 验证维度；造 10 条近义题型名入库查 top-1 验证命中。
2. **配置 + 依赖**：`requirements.txt` + `cos-python-sdk-v5`；`settings.py` + `COS_VECTORS_*`；`.env.example` 同步；`.env` 填真实值。
3. **核心模块**：`models/vector.py`（契约，`vector_type` 必填）+ `core/tutoring/vector_store.py`（embedding + CosVectorsClient + 路由）。
4. **端点**：`api/vector.py`（2 端点，`x-internal-token`）+ `main.py` 注册。
5. **测试 + 联调**：单测（mock embedding/COS）+ 与后端 Java 桥联调（put → query 近邻命中）。
6. **回滚**：停用向量端点即可——Java 桥降级回退字符规则 + 原样落库，主链路（题目落库/掌握表/接口）不依赖向量（后端 design 风险项已确认）。

## Open Questions（spike 已收口 2026-08-18）

- ✅ **`CosVectorsClient` 签名**：`CosConfig(Region, SecretId, SecretKey)` → `CosVectorsClient(config)`；`put_vectors(Bucket, Index, Vectors)` / `query_vectors(Bucket, Index, QueryVector, TopK, Filter, ReturnDistance, ReturnMetaData, ...)` 返回 `(resp, data)`，命中在 `data["vectors"]`。
- ✅ **建索引**：控制台已建 `topic-index`（`get_index` 实测 `dataType=float32, dimension=768, distanceMetric=cosine`）；SDK 另有 `create_index(Bucket, Index, DataType, Dimension, DistanceMetric, ...)` 可作备选。
- ✅ **distance 语义**：`distanceMetric="cosine"`，**distance 越小越相似，self 命中 ≈ 0**。实测示例：鸡兔同笼→鸡兔同笼问题 0.077 / 笼中鸡兔 0.096；一元二次方程求解→解一元二次方程 0.026 / 一元二次方程 0.061；行程问题→相遇问题 **0.332 边界**、异型（鸡兔同笼）0.481——**同型与异型在 ~0.3~0.48 之间有清晰间距，阈值区间可用**。
- ✅ **子账号密钥权限**：需授权（附 `QcloudCOSFullAccess` 后 get/put/query/delete 全通）。
