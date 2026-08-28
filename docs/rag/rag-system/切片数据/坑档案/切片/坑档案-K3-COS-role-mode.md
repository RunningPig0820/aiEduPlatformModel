# 坑档案 K3 COS 向量桶 role mode 拒收普通对象

> summary: COS 向量桶 role mode 拒收普通对象：jsonl 副本方案从"传 COS"调整为"留本地"（BM25/反查本地读）
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: K3. COS 向量桶 role mode 拒收普通对象
> 模块: rag-system ｜ 节: 坑档案
> COS路径: rag-slices/rag-system/坑档案/坑档案-K3-COS-role-mode.md
> 类别：开发难点
> target: 开发对账

---

**坑**：设计时想"jsonl 语料副本传 COS 普通对象 `rag/{version}/rag_slices.jsonl`"（供 BM25/反查运行时拉取），实测 `put_object` 报 `AccessDenied: bucket is role mode`。
**根因**：向量桶（Vertex Bucket）是 role mode，**只服务向量 API，拒普通对象写入**。
**解决**：jsonl 副本留本地 `scripts/rag/data/rag_slices.jsonl`（本就是 build 输入，BM25/反查从本地读）；tasks.md 1.6A 同步调整说明。
**证据**：`dea1c23`（纯 COS 入桶 + 调整说明）
