# 多路召回与RRF重排

> summary: 多路召回与RRF重排（design-python-project-intro-rag）：向量+BM25多路互补构成天然降级链、打分公式（相似度×问题类型×页面锚定加权）、阈值0.75/0.5、08-25已用RRF融合替代weighted-sum
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-python-intro-rag-06-多路召回与RRF重排.md
> 类别：架构设计

---

### D5. 打分

> 检索摘要：小语料怎么打分区分命中与超范围？score=similarity×问题类型匹配×页面锚定加权，索引层top-K1~3源文档3~5，阈值0.75/0.5，不需要重排模型

`score = similarity × 问题类型匹配 × 页面锚定加权`。
- 索引层池 top-K=1~3,源文档池 top-K=3~5。
- 阈值:索引层 0.75 / 源文档池 0.5。
- **为什么**:小语料不需要重排模型;多信号加权 + 阈值已足够区分命中与超范围。

### Requirement: 多路召回(向量 + BM25)

> 检索摘要：为什么向量+BM25多路召回互补？向量捕捉语义、BM25捕捉精确关键词，双路构成天然降级链——向量召回落空时关键词路仍能兜底，避免单路失效导致全链路空

- 系统 SHALL 在检索时融合向量召回与 BM25 关键词召回(jieba 分词)。
- 设计意图(为什么双路互补):向量捕捉语义、BM25 捕捉精确关键词,**双路互补构成天然降级链**——向量召回落空时关键词路仍能兜底,避免单路失效导致全链路空。
- 与 D10 的关系:D10 将关键词作为 COS 检索失败后的**降级兜底**;本块是正常检索路径上的**双路并行召回**,两处口径互补不冲突。

#### Scenario: 关键词兜底向量
- **WHEN** 向量召回落空或置信度低但关键词(如"防作弊""Neo4j")命中
- **THEN** 系统 SHALL 返回关键词命中的 chunk 作为补充结果

### Requirement: 打分与阈值 Scenario + 08-25 RRF 演进注

> 检索摘要：打分阈值的边界场景？索引层综合分≤0.75或源文档池≤0.5判定未覆盖进入范围门；08-25 已用 RRF 融合替代 weighted-sum（代码score=RRF×authority×anchor_w）

- 演进注(来自 08-21 源头素材):本 spec「打分 = 相似度 × 问题类型匹配 × 页面锚定加权」为 08-21 weighted-sum 口径,**08-25 已采用 RRF 融合替代 weighted-sum**(代码 `score = RRF × authority × anchor_w`),引用本 0.7 素材请核对代码确认实际落地状态。

#### Scenario: top-K 与阈值
- **WHEN** 索引层池所有候选综合分 ≤ 0.75,或源文档池所有候选综合分 ≤ 0.5
- **THEN** 系统 SHALL 判定为未覆盖,不返回结果并进入范围门边界流程

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-python-project-intro-rag.md`（§D5/§补充 retrieval-多路召回/§补充 retrieval-打分与阈值+08-25RRF演进注）
