## ADDED Requirements

### Requirement: 双池检索

系统 SHALL 提供两个检索池：索引层池（`doc_type=qa`，引导问题的可控答案）和源文档池（`doc_type=source`，自由问题的纯 RAG 检索）。

#### Scenario: 引导问题命中索引层池

- **WHEN** 用户点击引导问题（页面模式）
- **THEN** 系统 SHALL 在索引层池内检索，优先返回对应 QA 条目及其答案要点

#### Scenario: 自由问题命中源文档池

- **WHEN** 用户自由输入问题且未在索引层池高置信命中
- **THEN** 系统 SHALL 在源文档池内全文检索，返回命中的源文档 chunk

### Requirement: 页面锚定

系统 SHALL 支持页面模式与全局模式：前端传 `page` 时锁定该页检索范围；未传或跨页问题时全局检索。

#### Scenario: 页面模式锁页

- **WHEN** 前端传入 `page=知识图谱` 且问题为该页相关
- **THEN** 检索 SHALL 只在该页面的 `qa`/`source` chunk 内进行，不返回其他页面结果

#### Scenario: 全局模式跨页

- **WHEN** 问题跨页（如"知识图谱怎么支撑AI答疑"）或未传 page
- **THEN** 系统 SHALL 跨页检索，并可按来源页区分命中结果

### Requirement: 引导问题变体匹配

系统 SHALL 支持 UI 引导问题（变体文案）通过向量检索匹配到索引层的规范问题，而非按问题 ID 直连答案。

#### Scenario: 变体文案语义匹配

- **WHEN** UI 引导问题为"你们为什么拆成三段"而索引层规范问题为"为什么拆 decide/generate/question-understand"
- **THEN** 系统 SHALL 通过向量检索命中该规范问题条目（走同一检索管道）

### Requirement: 多路召回

系统 SHALL 在检索时融合向量召回与 BM25 关键词召回（jieba 分词）。

#### Scenario: 关键词兜底向量

- **WHEN** 向量召回落空或置信度低但关键词（如"防作弊""Neo4j"）命中
- **THEN** 系统 SHALL 返回关键词命中的 chunk 作为补充结果

### Requirement: 打分与阈值

系统 SHALL 计算 `相似度 × 问题类型匹配 × 页面锚定加权` 综合分，索引层池取 top-K 1~3、源文档池取 top-K 3~5。

#### Scenario: top-K 与阈值

- **WHEN** 索引层池所有候选综合分 ≤ 0.75，或源文档池所有候选综合分 ≤ 0.5
- **THEN** 系统 SHALL 判定为未覆盖，不返回结果并进入范围门边界流程

### Requirement: 范围门边界回答

系统 SHALL 在检索未覆盖时返回预写边界话术，不编造答案。

#### Scenario: 超范围拒绝

- **WHEN** 问题未命中任何高置信条目（如"题库做了吗"）
- **THEN** 系统 SHALL 返回预写边界话术（"目前覆盖了 知识图谱/AI答疑/组织中心/学生知识点分析，你可以问我…"），不输出虚构内容
