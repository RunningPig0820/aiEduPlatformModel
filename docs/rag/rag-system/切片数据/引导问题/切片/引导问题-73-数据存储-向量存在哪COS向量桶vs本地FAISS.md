# 向量存在哪？COS 向量桶 vs 本地 FAISS 怎么选？

> summary: 向量存在哪？COS 向量桶 vs 本地 FAISS 怎么选？
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-73-数据存储-向量存在哪COS向量桶vs本地FAISS.md
> 类别：数据存储

---

## 回答

**核心结论**：落地向量在 COS 向量桶 rag-1318177119（rag-full/rag-slice 两个物理索引、768d/float32/cosine）、原文在普通桶 ai-edu-1318177119（rag-source/ 源语料 + rag-slices/ 切片视图）；方案：生产走 COS、demo 默认本地 FAISS + 索引抽象层同接口兜底（断网/COS 挂）。

**分层展开**：
- **落地存储**：向量桶 `rag-1318177119` 双物理索引 rag-full/rag-slice（768d/float32/cosine），靠 module 标签 + query 侧 COS Filter 隔离；原文普通桶 `ai-edu-1318177119`（`rag-source/<模块>/...` 源语料 + `rag-slices/<模块>/...` 切片视图），前端"查看原文"走 `/api/rag/source/{key}` 读该桶（依据：分析-03 settings.py:88-115）。
- **方案兜底**：语雀方案 §12：生产走 COS、demo 默认本地 FAISS + 索引抽象层同接口兜底（断网/COS 挂可切本地）——抽象层保证两种后端同接口（依据：语雀总揽 §12/§8）。
- **特性注意**：COS 向量写入 10s 异步生效、写完立即 query 会 miss，demo 前需预建索引/等待生效；脚本不建索引，索引须控制台预建（依据：分析-03 隐性坑5/6）。
- **本地 jsonl 留底**：向量桶 role mode 不收普通对象（K3，put_object AccessDenied），语料 jsonl 留本地 `scripts/rag/data/` 供 BM25/反查读，原文才走普通桶（依据：坑档案 K3 / 分析-03）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 73 问）｜ `1.语雀/语雀-方案总揽.md`（§12/§8）｜ `3.代码/分析-03-索引与向量库.md` ｜ `5.难点/坑档案-开发与验证.md`（K3）
