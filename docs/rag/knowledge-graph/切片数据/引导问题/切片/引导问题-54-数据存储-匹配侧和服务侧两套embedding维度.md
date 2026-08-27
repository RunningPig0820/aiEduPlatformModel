# 匹配侧和服务侧两套 embedding 维度为什么不一致？各是多少维？

> summary: 数据存储引导问题回答：匹配侧 bge-small-zh-v1.5 本地 512 维（离线批量粗筛，kg_vectors.npy 1295×512），服务侧 dashscope text-embedding-v3 768 维（在线 RAG，写 COS）；各管一段互不通用，索引维度建好不可改
> 权威度: 1.0（合成问答答案切片，非原始证据）
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/引导问题/引导问题-54-数据存储-匹配侧和服务侧两套embedding维度.md
> 类别：数据存储

**核心结论**：匹配侧 bge-small-zh-v1.5 本地 512 维（离线批量粗筛，kg_vectors.npy 1295×512），服务侧 dashscope text-embedding-v3 768 维（在线 RAG，写 COS）；两套各管一段、维度不同互不通用，索引维度构建期定死不可改。

## 分层展开
- **匹配侧**：BAAI/bge-small-zh-v1.5 本地 512 维（`VECTOR_DIM=512`），预构建 `kg_vectors.npy`(1295×512) + `kg_texts.json` + `kg_concepts.json` + `index_meta.json`（含 MD5 checksum）（依据：分析-09 代码事实）
- **服务侧**：dashscope `text-embedding-v3` + `dimensions=768` 显式指定（模型默认 1024），写 COS 向量桶；返回向量长度 !=768 抛 RuntimeError（依据：分析-09 代码事实）
- **为什么不一致**：匹配侧要本地批量、免费、快（bge 512，离线管道）；服务侧要在线、准确、与业务索引一致（dashscope 768，在线服务）——一个离线管道、一个在线服务，互不干扰（依据：分析-09 设计要点）
- **维度约束**：COS 索引维度建好不可改，换 embedding 模型/维度必须重建索引；checksum 失配强制重建（依据：分析-09 隐性坑 / 引导问题.md 数据存储）
- **服务侧另一处**：题型向量（question-analysis 模块）复用 dashscope 768 维，同样必须显式 768（依据：分析-09 服务侧 / 口径参考）

## 追问防御
- **可能追问：维度不一致怎么办？** → 索引构建期定死，换模型必须重建索引，checksum 失配强制重建；服务侧 768 与匹配侧 512 两套独立，别混用（依据：引导问题.md 数据存储 / 分析-09 隐性坑）
- **可能追问：两套向量混了会怎样？** → 512/768 维度不同互相不通用，混用会维度报错/语义错位，路由靠 vector_type 区分（依据：引导问题.md 数据存储可能防御）

> 证据：详见 `4.完善文档/02-知识图谱数据入库主流程.md`（存储拓扑表）｜ `3.代码/分析-09-向量索引构建与校验.md`
