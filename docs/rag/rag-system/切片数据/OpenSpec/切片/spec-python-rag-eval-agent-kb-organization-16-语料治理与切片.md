# 语料治理与切片（模块清单状态机 + 完善文档 + 切片索引）
> summary: 语料治理与切片（知识库整理）：维护5个模块清单与状态机 pending→evaluated 持久化到状态文件，逐个模块产出8节完善文档，复用切片器/嵌入/COS索引产出可检索chunk。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-rag-eval-agent-kb-organization-16-语料治理与切片.md
> 类别：操作流程

---

### 模块清单与状态机
> 检索摘要：知识库模块清单固定5个（知识图谱/AI答疑/题型知识点/组织中心/RAG问答系统），每模块状态机 pending→evaluated 持久化到状态文件，语料变更后已索引模块回退为 chunked 待重索引。

系统 SHALL 维护知识库模块清单（知识图谱 / AI答疑 / 题型知识点 / 组织中心 / RAG 问答系统），并为每模块跟踪整理状态：`pending → organized → chunked → indexed → evaluated`，持久化到状态文件。

#### Scenario: 状态推进

- **WHEN** 某模块完成完善文档产出
- **THEN** 该模块状态 SHALL 从 `pending` 变为 `organized`

#### Scenario: 语料变更使索引失效

- **WHEN** 某模块完善文档被修改（已索引之后）
- **THEN** 该模块状态 SHALL 从 `indexed` 回退为 `chunked`（待重索引），避免用旧索引评测

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-eval-agent-kb-organization.md`（§模块清单与状态机）

---

### 完善文档产出
> 检索摘要：完善文档按8节结构（定位/核心功能/为什么/数据流转含mermaid/技术实现/坑/规模/权限）逐个模块产出，检查需8节齐全且"为什么/数据流转/坑"三节有实质内容。

系统 SHALL 支持逐个模块产出完善文档（8 节结构：定位/核心功能/为什么/数据流转含mermaid/技术实现/坑/规模/权限），且每节非空模板。

#### Scenario: 完善文档完整

- **WHEN** 检查任意模块完善文档
- **THEN** 8 节齐全，且「为什么」「数据流转」「坑」三节有实质内容

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-eval-agent-kb-organization.md`（§完善文档产出）

---

### 切片与索引复用
> 检索摘要：复用 project-intro-rag 的切片器/嵌入/COS 索引把完善文档产出可检索 chunk 并写入索引，模块处于 indexed 状态即可用 rag-retrieval 检索到。

系统 SHALL 复用 `project-intro-rag` 的切片器/嵌入/COS 索引，将完善文档产出可检索 chunk 并写入索引。

#### Scenario: 模块可检索

- **WHEN** 某模块处于 `indexed` 状态
- **THEN** 该模块完善文档 SHALL 已切片入库，可用 rag-retrieval 检索到

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-eval-agent-kb-organization.md`（§切片与索引复用）
