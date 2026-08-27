# 向量索引与 embedding

> summary: 向量索引(bge 本地 512 维 + dashscope text-embedding-v3 768 维服务侧 RAG; 预构建索引 10MB vs 懒加载 3.5GB; checksum MD5 失配回退懒加载; 单次检索 <10ms)
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-方案总揽-9-向量索引与embedding.md
> 类别：数据存储

---

### 9. 向量索引与 embedding

- **匹配侧（bge 本地）**：`BAAI/bge-small-zh-v1.5`，`VECTOR_DIM=512`，numpy 暴力搜索（≤5000 条 <10ms）+ sentence-transformers；粗筛 top-20。资源：模型 2.5GB + 向量 5000×512×4B≈10MB，总计约 3.5GB。
- **索引文件**：`kg_vectors.npy`（形状 1295×512）/`kg_texts.json`/`kg_concepts.json`/`index_meta.json`；构建约 60 秒（预构建一次、多次复用）。
- **懒加载 vs 预构建**：`LocalVectorRetriever`（懒加载）每次运行加载模型构建向量，内存约 3.5GB、单次检索 <10ms；`PrebuiltIndexRetriever`（预构建，`--use-prebuilt-index`）仅加载 numpy 约 10MB、单次检索 <5ms。
- **checksum**：MD5（按 uri+label 排序拼接）存 `index_meta.json['neo4j_checksum']`，用于索引有效性校验；失配强制回退懒加载重建。
- **服务侧 RAG embedding（dashscope）**：`text-embedding-v3`、768 维（显式，模型默认 1024），base `https://dashscope.aliyuncs.com/compatible-mode/v1`；答疑/掌握度服务侧向量检索用。
- **维度口径**：bge 512 维（匹配侧本地）、dashscope 768 维（服务侧 RAG）；索引维度固定不可改。

> 证据：详见 `1.语雀/语雀-方案总揽.md`（§9）
