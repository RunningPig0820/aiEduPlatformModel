# 双池检索设计

> summary: 双池检索设计（design-python-project-intro-rag）：索引层池（预写QA可控）+源文档池（纯RAG），同写一个COS索引用doc_type区分，引导问题命中QA/自由问题命中源文档
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-python-intro-rag-03-双池检索设计.md
> 类别：架构设计

---

### D2. 双池检索(索引层池 + 源文档池)

> 检索摘要：为什么项目介绍RAG要分索引层池和源文档池？索引层QA预写保证引导问题可控，源文档池全文保证自由问题纯RAG，两池同写COS索引用doc_type区分

- **索引层池**:每页 5~8 条 QA 条目(`问题 + 答案要点 + 引用`),doc_type=`qa`。引导问题命中它 → 答案可控、上下文小、便宜。
- **源文档池**:完善文档全文,doc_type=`source`。自由问题命中它 → 纯 RAG 真发挥。
- 两池同写一个 COS 索引,用 `doc_type` metadata 区分。
- **为什么**:引导问题要稳定可控,自由问题要证明 RAG——一池满足不了两个目标。
- **备选**:只有索引层 → 自由问题全变边界回答,RAG 能力没证据;只有源文档池 → 引导问题不可控易翻车。

### Requirement: 双池检索 Scenario 明细（补池间路由条件）

> 检索摘要：双池之间怎么路由？点击引导问题（页面模式）走索引层池优先返回QA条目；自由问题且未在索引层池高置信命中走源文档池全文检索

#### Scenario: 引导问题命中索引层池
- **WHEN** 用户点击引导问题(页面模式)
- **THEN** 系统 SHALL 在索引层池内检索,优先返回对应 QA 条目及其答案要点

#### Scenario: 自由问题命中源文档池
- **WHEN** 用户自由输入问题且未在索引层池高置信命中
- **THEN** 系统 SHALL 在源文档池内全文检索,返回命中的源文档 chunk

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-python-project-intro-rag.md`（§D2/§补充 retrieval-双池检索Scenario明细）
