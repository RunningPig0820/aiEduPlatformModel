# 本地 embedding 内存 3.5GB 是怎么压到预构建索引的？
> summary: 开发难点引导问题回答：把"模型加载+全量 encode 1295 概念"的重复重活沉淀成离线产物 kg_vectors.npy（512 维）+index_meta.json，运行期只读文件约 3.1MB/启动<5ms；3.5GB→3.1MB 不是模型变小，是预计算结果落盘
> 权威度: 1.0（合成问答答案切片，非原始证据）
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/引导问题/引导问题-26-开发难点-本地embedding内存35GB是怎么.md
> 类别：开发难点

**核心结论**：把"模型加载 + 全量 encode 1295 个图谱概念"这种每次运行都重复的重活沉淀成离线产物——`build_vector_index.py` 一次性构建落盘 `kg_vectors.npy`（1295×512 维）+ `index_meta.json`（含 MD5 checksum），运行期只读文件约 3.1MB、启动 <5ms；3.5GB→3.1MB 不是模型变小了，而是**把预计算结果落盘、运行期只保留查询编码**。

## 分层展开
- **懒加载痛点**：LocalVectorRetriever 每次匹配启动都"加载 bge-small-zh-v1.5 模型 + 全量 encode 1295 概念"，进程内存约 3.5GB、启动约 60s——同一份图谱数据多次匹配间根本没变，属于重复计算（依据：坑档案 J-KG7 / 分析-09）。
- **解法**：build_vector_index.py 一次性构建 → 落盘 kg_vectors.npy（512 维）/kg_texts.json/kg_concepts.json/index_meta.json；匹配时 `--use-prebuilt-index` 走 PrebuiltIndexRetriever，只 `np.load` 预置向量（依据：坑档案 J-KG7 / 分析-09）。
- **效果**：预构建索引文件实测约 3.1MB（npy 2.6MB + json）、单次检索 <5ms（注释口径）——与懒加载 3.5GB 相比主要省的是 1295 个概念的 encode 时间和内存（依据：分析-09 / 完善文档 04）。
- **checksum 防呆**：index_meta.json 含 neo4j_checksum（MD5(uri+label 按 uri 排序拼接)），匹配启动时用当前 Neo4j 概念实时算指纹比对，失配则告警"索引已过期"回退懒加载或 `--force` 重建（依据：坑档案 J-KG7 / 分析-09）。
- **口径提醒（翻转）**：方案/代码注释称"预构建约 10MB"，实际索引文件约 3.1MB——10MB 是注释口径偏大；且 PrebuiltIndexRetriever 查询时仍需加载模型做查询编码，首次启动仍要读模型文件（依据：完善文档 04 / 分析-09）。

## 追问防御
- **可能追问：索引过期怎么办？** → checksum 失配告警并回退懒加载（3.5GB），或 `--force-build-index` 重建；宁可回退慢的懒加载也不拿脏索引静默匹配（依据：完善文档 04 / 分析-09）。
- **可能追问：索引维度能改吗？** → 索引构建期定死 512（VECTOR_DIM=512），换模型/维度必须重建索引，checksum 失配会强制重建（依据：分析-09 / 引导问题.md 4）。
- **可能追问：预构建后还加载模型吗？** → 需要——PrebuiltIndexRetriever 只省了全量 encode，查询编码仍需 SentenceTransformer 模型加载（依据：分析-09）。

> 证据：详见 `4.完善文档/04-数据清洗与质量保障.md` ｜ `3.代码/分析-09-向量索引构建与校验.md` ｜ `5.难点/坑档案.md（J-KG7）`
