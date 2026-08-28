# 多路召回与RRF重排
> summary: 多路召回与RRF重排
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-rag-project-intro-assistant-pipeline-06-多路召回与RRF重排.md
> 类别：架构设计

---

## 文档说明
> 本文件由 OpenSpec 设计素材（spec-python-rag-project-intro-assistant-pipeline.md）按业务主题「多路召回与RRF重排」重切合并。
> ⚠️设计阶段素材：真实实现以权威度 0.8 的 canonical 真相源 + 代码为准（代码已部分落地）；含 ✅已落地 / ⚠️构想未实现 / ❓待决策 内容，引用需核对代码。

### Requirement: 按 anchor 选语料池的多路召回
> 检索摘要：多路召回怎么按 anchor 选语料池——向量+BM25 双路、单路 2s 超时降级、池内锚定加权？

系统 SHALL 执行向量（COS rag 索引）与 BM25（本地 jsonl + jieba）双路召回，且**先按 intent 的 anchor（模块）过滤语料池**（orchestrate 入参加 `corpus`），池内继续 authority × 节级锚定加权；任一单路 2s 硬超时/异常 → 该路降级为空（`{hits:[], confidence:0}`）继续另一路。anchor 缺失/ambiguous → 维持全池现状。

#### Scenario: 双路正常
- **WHEN** 两路均在 2s 内返回
- **THEN** 编排器 RRF 融合两路，池内锚定加权生效

#### Scenario: 单路降级
- **WHEN** 向量路超时/挂掉
- **THEN** 降级纯 BM25，链路继续，rerank 事件带 degraded 标记

#### Scenario: anchor 选池
- **WHEN** intent anchor="ai-tutoring"
- **THEN** 仅在该模块语料池内召回（当前 234 块），池内继续节级锚定加权

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-pipeline.md`（§Requirement: 按 anchor 选语料池的多路召回）

### Requirement: RRF 精排 Top-K 仅回传精排块
> 检索摘要：RRF 精排后回传什么——只回传 Top-K 精排块、严禁吐全量召回列表？

系统 SHALL 对双路召回 RRF 融合（`RRF_K`），按综合分取 Top-K（默认 3），**仅回传精排后块**（blockId/title/summary/filePath/score）；严禁吐全量召回列表。

#### Scenario: 仅回传精排块
- **WHEN** 双路命中多块
- **THEN** `rerank` 事件仅携带 Top-K 精排块

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-pipeline.md`（§Requirement: RRF 精排 Top-K 仅回传精排块）
