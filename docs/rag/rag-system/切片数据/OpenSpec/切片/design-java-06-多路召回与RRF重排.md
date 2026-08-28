# 多路召回与RRF重排

> summary: 多路召回与RRF重排（design-java-rag-project-intro-assistant）：双池三路（rag-full全量向量+rag-slice切片向量+BM25本地关键词）多路召回、RRF融合常数RRF_K、Top-K默认3可配、rerank事件仅回传精排块
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-06-多路召回与RRF重排.md
> 类别：架构设计

---

### Requirement: 多路召回（落地说明 + rerank degraded 标记）

> 检索摘要：多路召回落地为双池三路（rag-full全量向量+rag-slice切片向量+BM25本地关键词），各向量路2s超时降级，语义兼容并超越原双路设计；单路降级时rerank事件带degraded标记

目标 D7 已定义向量/Bm25 单路各 2s 硬超时与 `{hits:[], confidence:0}` 冒泡降级语义。本块独有:
- **落地说明**:当前实现为**双池三路**(rag-full 全量向量 + rag-slice 切片向量 + BM25 本地关键词),各向量路 2s 超时降级;语义兼容并超越原双路设计。
- **rerank degraded 标记**:单路超时/异常 → 该路降级为空并继续另一路,链路继续,`rerank` 事件携带 degraded 标记(前端可展示"该步降级")。

### Requirement: RRF 精排 Top-K（K 默认值与 rerank 事件字段）

> 检索摘要：RRF融合常数沿用RRF_K按综合分取Top-K默认K=3可配，rerank事件仅携带精排块blockId/title/summary/filePath/score，严禁把全量召回列表吐给前端

目标 D4 已定义 RRF 精排 top-K 与阈值(0.75/0.5),但未定 K 默认值与事件字段。本块独有:系统 SHALL 对双路召回结果做 RRF 融合(融合常数沿用 `RRF_K`),按综合分取 Top-K(**默认 K=3,可配**),仅将精排后块回传;**严禁将全量召回原始列表吐给前端**。`rerank` 事件仅携带精排 Top-K 块(`blockId/title/summary/filePath/score`)。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§补充 pipeline-多路召回 / §补充 pipeline-RRF精排Top-K）
