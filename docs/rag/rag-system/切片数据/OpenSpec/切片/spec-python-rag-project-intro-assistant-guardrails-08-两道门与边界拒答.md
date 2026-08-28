# 两道门与边界拒答
> summary: 两道门与边界拒答
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-rag-project-intro-assistant-guardrails-08-两道门与边界拒答.md
> 类别：业务流程

---

### Purpose
> 检索摘要：白盒助手边界怎么控制？模块全放行由语料驱动、范围门低置信度过滤是唯一拒答路径、clarify 澄清轮加 is_quoted 确定性引用。

模块全放行（AI答疑/RAG/题型/知识图谱无禁区，语料驱动）+ 范围门低置信度过滤（唯一拒答路径）+ clarify 澄清轮 + is_quoted 确定性引用硬匹配。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-guardrails.md`（§Purpose）

### 模块全放行与硬路由
> 检索摘要：白盒助手能问哪些模块？AI答疑/RAG/题型/知识图谱四模块全放行不硬拒答，涉及架构/代码/部署/评测/接口则强制路由 RAG 项目知识库。

系统 SHALL 放行 AI答疑/RAG/题型/知识图谱四模块提问（无禁区），intent 路由到对应模块语料池；问题涉及"系统架构/代码实现/部署流程/评测方案/接口设计" → 强制路由 RAG 项目知识库。模块可否答由语料决定，意图层不硬拒答任何模块。

#### Scenario: 四模块放行
- **WHEN** 学生问 AI答疑/RAG/题型/知识图谱任一模块
- **THEN** intent 路由对应模块，进入召回；意图层不拒答任何模块

#### Scenario: 涉及架构路由至 RAG
- **WHEN** 问题涉及"系统架构/代码实现/部署流程/评测方案/接口设计"
- **THEN** intent 强制路由 RAG 项目知识库

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-guardrails.md`（§模块全放行与硬路由）

### 范围门低置信度过滤（唯一拒答路径）
> 检索摘要：范围门低置信度过滤怎么判定拒答？基于召回置信度（向量<0.75 且 BM25<0.5 双路低于阈值）而非 rerank RRF 分，是唯一拒答路径。

系统 SHALL 在召回后判定是否低置信（**基于召回置信度 0-1，非 rerank 的 RRF 相对分**）：rerank 空（无语料模块）→ 直接拒答；非空但**向量置信度 <0.75 且 BM25 置信度 <0.5**（双路都低于阈值）→ 拒答；单路达阈值即通过。拒答 → 固定话术"未找到关联文档，我尚未掌握"，`boundary` 事件（reason=low_confidence），消耗 recall token 但**不调 generate**。此为本助手唯一拒答路径（无禁区硬拒答）。

> **阈值语义校正（2026-08-25）**：初版误用 rerank 的 RRF 融合分（量级 0.01~0.05，`1/(RRF_K+rank)×authority×anchor_w`，天花板也够不到 0.75）比对 0.75/0.5 → 所有命中都误判低置信拒答。改为**召回置信度**（向量 = 1-平均余弦距离 / BM25 = 归一 top-score），0-1 量级与 spec 原意对齐。

#### Scenario: 无语料模块低置信
- **WHEN** 问知识图谱且其无切片语料（命中空/低置信）
- **THEN** `boundary` + low_confidence 固定话术，无生成 token

#### Scenario: 语料未覆盖边角问题
- **WHEN** 语料存在但双路召回置信度都低于阈值（vec <0.75 且 bm <0.5）
- **THEN** `boundary` + low_confidence 固定话术，无生成 token

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-guardrails.md`（§范围门低置信度过滤（唯一拒答路径））

### 固定话术不调 LLM
> 检索摘要：拒答话术为什么写死不调 LLM？边界拒答/超时降级话术固定，严禁 LLM 生成保证 0 token 零成本。

系统 SHALL 将拒答/超时降级话术写死，严禁调 LLM 生成，保证 0 token。

#### Scenario: 拒答零成本
- **WHEN** 任一拒答分支触发
- **THEN** 写死话术，tokens_usage 全 0

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-guardrails.md`（§固定话术不调 LLM）

### 模块可用性数据驱动
> 检索摘要：模块语料后补会自动变可答吗？语料存在性决定模块可否答，无语料走低置信过滤，切片入库后自动可答无需改代码。

系统 SHALL 由语料存在性决定模块可否答：无语料模块正常进入召回但命中空/低置信 → 低置信过滤；未来语料入库切片 → 自动可答（无代码改动）。

#### Scenario: 语料后补自动可答
- **WHEN** RAG 模块语料切片入库后
- **THEN** 该模块提问从低置信拒答变为正常召回回答

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-guardrails.md`（§模块可用性数据驱动）
