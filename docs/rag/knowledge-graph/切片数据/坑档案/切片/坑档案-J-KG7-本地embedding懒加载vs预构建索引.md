# 坑档案-J-KG7-本地embedding懒加载vs预构建索引

> summary: 本地embedding懒加载vs预构建索引
> 来源: 坑档案 ｜ 锚点: J-KG7 ｜ 节: 5.难点/坑档案.md
> COS路径: rag-slices/knowledge-graph/坑档案/坑档案-J-KG7-本地embedding懒加载vs预构建索引.md
> 类别：开发难点
> target: 开发对账

---

**1. 问题现象**：每次跑匹配脚本都要等 ~60 秒加载 sentence-transformers 模型 + 预计算图谱向量，进程内存冲到 ~3.5GB；反复跑同一批数据浪费严重。

**2. 触发流程**：`match_textbook_kp.py` 启动 → `KPMatcher._init_vector_retriever`（`kp_matcher.py:469-518`）→ 默认懒加载模式 `LocalVectorRetriever`：加载 BAAI/bge-small-zh-v1.5 + encode 全部图谱概念向量（`kp_matcher.py:107-113`）。

**3. 根因分析**：懒加载每次运行都"模型加载 + 向量重算"，图谱概念 1295+ 条、向量维度 512（`vector_index_manager.py:23 VECTOR_DIM=512`），encode 全量 + 内存常驻 ≈ 3.5GB、启动 ~60s；而同一份图谱数据在多次匹配间根本没变，属于**重复计算**。`kp_matcher.py:63-75` `LocalVectorRetriever` docstring 明写"内存占用约 3.5GB"。

**4. 排查过程**：看启动日志"加载向量检索模型 / 预计算 N 个图谱知识点的向量"，估算 30s 模型加载 + 30s 向量计算；对照多次运行发现每次都在做同样的事。

**5. 解决方案 & 改动点**：**预构建索引 + checksum 校验**：`build_vector_index.py` 一次性 build → 落盘 `kg_vectors.npy`（512 维）/`kg_texts.json`/`kg_concepts.json`/`index_meta.json`（含 `neo4j_checksum`，`vector_index_manager.py:147-153`）→ 匹配时 `--use-prebuilt-index` 走 `PrebuiltIndexRetriever`（`kp_matcher.py:150-232`，"内存占用约 10MB、启动 <5ms"）。**checksum 防呆**：`check_index_validity`（`kp_matcher.py:443-467`）用 `_compute_checksum`（uri+label 排序拼串 MD5，`vector_index_manager.py:204-218`）比对当前 Neo4j 概念与索引 meta 里的 checksum，不匹配则日志告警"索引已过期"并回退懒加载/建议 `--force` 重建（`kp_matcher.py:462-465`、`match_textbook_kp.py:283-295`）。提交：`126d210 [知识图谱]-[添加 sentence-transformers 模型]`、`03f3f75`（vector_index_manager.py 创建）。

**6. 面试口述要点**：**可重复计算要缓存到"结果"而不只是"过程"**——把"模型加载 + 向量全量编码"这种重活沉淀成离线产物，运行期只读文件；3.5GB→10MB 不是模型变小了，而是**把预计算结果落盘、运行期只保留查询编码**。checksum 解决的是缓存一致性：索引必须和它依赖的 Neo4j 数据快照绑定，数据变了要么重建要么回退，不能拿过期索引静默算错。面试可讲"索引维度 512 固定、索引建好不可改"的连带约束。
