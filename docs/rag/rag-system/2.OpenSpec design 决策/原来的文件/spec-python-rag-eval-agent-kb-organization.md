> summary: 知识库整理需求（spec）：维护5个模块清单与状态机（pending→organized→chunked→indexed→evaluated）持久化到状态文件、逐个模块产出8节完善文档、复用切片器/嵌入/COS索引产出可检索chunk，语料变更后状态回退待重索引。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-source/rag-system/OpenSpec设计决策/spec-python-rag-eval-agent-kb-organization.md
> 类别：数据关联

# spec-python-rag-eval-agent-kb-organization（知识库整理需求）

## 文档说明
> 本文件为原始spec文档的RAG结构化重构版本。
> ⚠️重要提示：本文属于**设计阶段素材**，同时包含✅已落地、⚠️构想未实现、❓待决策内容；业务真实实现请以权威度0.8的canonical真相源文档为准。本文件独立完整，内容不拆分到外部canonical文档。
> ⚠️代码演进说明：真实实现以 0.8 canonical + 代码为准（代码已演进：HIT_K=5 / 判分改硬算）。

### 模块清单与状态机
> 状态：⚠️
> 检索摘要：知识库模块清单固定5个（知识图谱/AI答疑/题型知识点/组织中心/RAG问答系统），每模块状态机 pending→evaluated 持久化到状态文件，语料变更后已索引模块回退为 chunked 待重索引。

系统 SHALL 维护知识库模块清单（知识图谱 / AI答疑 / 题型知识点 / 组织中心 / RAG 问答系统），并为每模块跟踪整理状态：`pending → organized → chunked → indexed → evaluated`，持久化到状态文件。

#### Scenario: 状态推进

- **WHEN** 某模块完成完善文档产出
- **THEN** 该模块状态 SHALL 从 `pending` 变为 `organized`

#### Scenario: 语料变更使索引失效

- **WHEN** 某模块完善文档被修改（已索引之后）
- **THEN** 该模块状态 SHALL 从 `indexed` 回退为 `chunked`（待重索引），避免用旧索引评测

### 完善文档产出
> 状态：⚠️
> 检索摘要：完善文档按8节结构（定位/核心功能/为什么/数据流转含mermaid/技术实现/坑/规模/权限）逐个模块产出，检查需8节齐全且"为什么/数据流转/坑"三节有实质内容。

系统 SHALL 支持逐个模块产出完善文档（8 节结构：定位/核心功能/为什么/数据流转含mermaid/技术实现/坑/规模/权限），且每节非空模板。

#### Scenario: 完善文档完整

- **WHEN** 检查任意模块完善文档
- **THEN** 8 节齐全，且「为什么」「数据流转」「坑」三节有实质内容

### 切片与索引复用
> 状态：⚠️
> 检索摘要：复用 project-intro-rag 的切片器/嵌入/COS 索引把完善文档产出可检索 chunk 并写入索引，模块处于 indexed 状态即可用 rag-retrieval 检索到。

系统 SHALL 复用 `project-intro-rag` 的切片器/嵌入/COS 索引，将完善文档产出可检索 chunk 并写入索引。

#### Scenario: 模块可检索

- **WHEN** 某模块处于 `indexed` 状态
- **THEN** 该模块完善文档 SHALL 已切片入库，可用 rag-retrieval 检索到
