## ADDED Requirements

### Requirement: 完善文档生成

系统 SHALL 支持为每个模块产出一份「完善版设计文档」，以语雀文档 + 代码注释 + OpenSpec 为事实源，人工/LLM 辅助补全语料空模板。

完善文档 SHALL 包含 8 个章节：产品定位、核心功能、为什么这么设计、数据流转（含预置 mermaid）、技术实现、关键坑与解法、数据规模与指标、权限与边界。

#### Scenario: 产出完善文档

- **WHEN** 用户为「知识图谱」模块生成完善文档
- **THEN** 系统 SHALL 输出一份包含全部 8 节的 markdown 文档，且「为什么这么设计」「数据流转」「关键坑与解法」三节有实质内容（非空模板）

#### Scenario: 冲突以代码为准

- **WHEN** 语雀文档描述与代码实现冲突
- **THEN** 完善文档 SHALL 以代码实现为准，并标注来源

### Requirement: 切片与 metadata

系统 SHALL 将完善文档按章节切分为检索单元（chunk），并为每个 chunk 标注 metadata：`page`（所属页面）、`doc_type`（`qa` 或 `source`）、`section`（章节）、`permissions`（权限标签）、`source_doc`（源文档全文）、`order`（叙事顺序）。

#### Scenario: 按章节切片

- **WHEN** 对完善文档执行切片
- **THEN** 每个 8 节章节 SHALL 独立成 chunk，且 `page`/`doc_type`/`section`/`source_doc` metadata 完整

#### Scenario: 切片保留源文档

- **WHEN** 任意 chunk 生成后
- **THEN** 该 chunk SHALL 携带 `source_doc`（源文档全文），用于展示「召回文档原文」面板

### Requirement: 嵌入与维度一致性

系统 SHALL 使用 dashscope text-embedding-v3（768 维）对 QA 条目与源文档 chunk 进行向量化，并保证同一索引内维度一致。

#### Scenario: 嵌入维度校验

- **WHEN** 对文本执行 embedding
- **THEN** 返回向量长度 SHALL 为 768，否则抛错拒绝写入

### Requirement: COS 向量索引构建

系统 SHALL 将向量写入 COS 向量桶 `rag-index`，索引构建支持 `--clear` 幂等重建，且支持 demo 前预建。

#### Scenario: 幂等重建

- **WHEN** 重复执行带 `--clear` 的索引构建
- **THEN** 索引 SHALL 被清空后重建，无残留旧数据

#### Scenario: 写入后不可即查的一致性约束

- **WHEN** 刚执行 put 后立即 query
- **THEN** 系统 SHALL 不保证命中（COS 异步生效），demo 环境 SHALL 使用预建索引

### Requirement: 索引层 QA 条目

系统 SHALL 支持从完善文档提炼索引层 QA 条目（每页 5~8 条），每条含：`question`（规范问题）、`answer_points`（答案要点）、`references`（引用源文档段落）。

#### Scenario: QA 条目提炼

- **WHEN** 为某页面生成索引层条目
- **THEN** 每条 SHALL 包含 question + answer_points + references，且数量在 5~8 条之间
