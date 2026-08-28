# 语料 jsonl 为什么留本地，不传 COS？

> summary: 语料 jsonl 为什么留本地，不传 COS？
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-49-数据存储-语料jsonl为什么留本地不传COS.md
> 类别：数据存储

---

## 回答

**核心结论**：K3：向量桶是 role mode **只服务向量 API、拒普通对象写入**（AccessDenied）；jsonl 留本地 `scripts/rag/data/` 供 BM25/反查读，原文才走普通桶。

**分层展开**：
- **坑**：设计时想"jsonl 语料副本传 COS 普通对象 `rag/{version}/rag_slices.jsonl`"（供 BM25/反查运行时拉取），实测 `put_object` 报 `AccessDenied: bucket is role mode`（依据：坑档案 K3）。
- **根因**：向量桶（Vertex Bucket）是 role mode，**只服务向量 API，拒普通对象写入**（依据：坑档案 K3）。
- **解决**：jsonl 副本留本地 `scripts/rag/data/`（本就是 build 输入，BM25/反查从本地读）；`tasks.md 1.6A` 同步调整说明；原文/切片视图才走普通桶 `ai-edu-1318177119`（依据：坑档案 K3 / 分析-03）。
- **关联**：COS metadata 不含 text（上限 10 字段/2048B），命中后全文也靠 key 反查本地 jsonl——jsonl 留本地是检索/回源的必要条件（依据：分析-03）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 49 问）｜ `4.完善文档/08-数据规模与指标.md` ｜ `3.代码/分析-03-索引与向量库.md` ｜ `5.难点/坑档案-开发与验证.md`（K3）
