> summary: 白盒助手 rag-assistant-guardrails 边界控制 spec：模块全放行由语料驱动，范围门低置信度过滤为唯一拒答路径，配 clarify 澄清轮、switch 切换与 is_quoted LCS 确定性引用，模块可用性数据驱动。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-source/rag-system/OpenSpec设计决策/spec-python-rag-project-intro-assistant-guardrails.md
> 类别：业务流程

# rag-assistant-guardrails Specification

## 文档说明
> 本文件为原始spec文档的RAG结构化重构版本。
> ⚠️重要提示：本文属于**设计阶段素材**，同时包含✅已落地、⚠️构想未实现、❓待决策内容；业务真实实现请以权威度0.8的canonical真相源文档为准。本文件独立完整，内容不拆分到外部canonical文档。

### Purpose
> 状态：⚠️
> 检索摘要：白盒助手边界怎么控制？模块全放行由语料驱动、范围门低置信度过滤是唯一拒答路径、clarify 澄清轮加 is_quoted 确定性引用。

模块全放行（AI答疑/RAG/题型/知识图谱无禁区，语料驱动）+ 范围门低置信度过滤（唯一拒答路径）+ clarify 澄清轮 + is_quoted 确定性引用硬匹配。

### 模块全放行与硬路由
> 状态：⚠️
> 检索摘要：白盒助手能问哪些模块？AI答疑/RAG/题型/知识图谱四模块全放行不硬拒答，涉及架构/代码/部署/评测/接口则强制路由 RAG 项目知识库。

系统 SHALL 放行 AI答疑/RAG/题型/知识图谱四模块提问（无禁区），intent 路由到对应模块语料池；问题涉及"系统架构/代码实现/部署流程/评测方案/接口设计" → 强制路由 RAG 项目知识库。模块可否答由语料决定，意图层不硬拒答任何模块。

#### Scenario: 四模块放行
- **WHEN** 学生问 AI答疑/RAG/题型/知识图谱任一模块
- **THEN** intent 路由对应模块，进入召回；意图层不拒答任何模块

#### Scenario: 涉及架构路由至 RAG
- **WHEN** 问题涉及"系统架构/代码实现/部署流程/评测方案/接口设计"
- **THEN** intent 强制路由 RAG 项目知识库

### 范围门低置信度过滤（唯一拒答路径）
> 状态：✅
> 检索摘要：范围门低置信度过滤怎么判定拒答？基于召回置信度（向量<0.75 且 BM25<0.5 双路低于阈值）而非 rerank RRF 分，是唯一拒答路径。

系统 SHALL 在召回后判定是否低置信（**基于召回置信度 0-1，非 rerank 的 RRF 相对分**）：rerank 空（无语料模块）→ 直接拒答；非空但**向量置信度 <0.75 且 BM25 置信度 <0.5**（双路都低于阈值）→ 拒答；单路达阈值即通过。拒答 → 固定话术"未找到关联文档，我尚未掌握"，`boundary` 事件（reason=low_confidence），消耗 recall token 但**不调 generate**。此为本助手唯一拒答路径（无禁区硬拒答）。

> **阈值语义校正（2026-08-25）**：初版误用 rerank 的 RRF 融合分（量级 0.01~0.05，`1/(RRF_K+rank)×authority×anchor_w`，天花板也够不到 0.75）比对 0.75/0.5 → 所有命中都误判低置信拒答。改为**召回置信度**（向量 = 1-平均余弦距离 / BM25 = 归一 top-score），0-1 量级与 spec 原意对齐。

#### Scenario: 无语料模块低置信
- **WHEN** 问知识图谱且其无切片语料（命中空/低置信）
- **THEN** `boundary` + low_confidence 固定话术，无生成 token

#### Scenario: 语料未覆盖边角问题
- **WHEN** 语料存在但双路召回置信度都低于阈值（vec <0.75 且 bm <0.5）
- **THEN** `boundary` + low_confidence 固定话术，无生成 token

### 固定话术不调 LLM
> 状态：⚠️
> 检索摘要：拒答话术为什么写死不调 LLM？边界拒答/超时降级话术固定，严禁 LLM 生成保证 0 token 零成本。

系统 SHALL 将拒答/超时降级话术写死，严禁调 LLM 生成，保证 0 token。

#### Scenario: 拒答零成本
- **WHEN** 任一拒答分支触发
- **THEN** 写死话术，tokens_usage 全 0

### clarify 澄清轮
> 状态：⚠️
> 检索摘要：问题模糊时怎么澄清？intent ambiguous 且候选≥2 触发 clarify 事件，固定话术加候选与默认项，不召回不生成只澄清一次。

系统 SHALL 在 intent `ambiguous=true` 且 candidates ≥2 时发 `clarify` 事件（固定话术 + candidates + default），不 recall/generate、0 token、不计答案轮次、写 history；下一条重跑 intent；仍模糊不再二次澄清，直接默认当前功能。

候选判定（C4 定稿）：主源 = intent LLM `candidates`（2~4 个模块闭集）；LLM 未给/给<2 → 会话最近 N 轮锚过模块去重兜底；仍 <2 → 不触发 clarify。default = current_project > 会话最后锚定。

#### Scenario: 多候选澄清
- **WHEN** 问"这个功能的流转"且会话内多功能候选
- **THEN** `clarify`（"您的问题涉及多个功能，请明确功能名。默认回答当前功能：RAG项目" + candidates + default）

#### Scenario: 澄清一次后仍模糊
- **WHEN** 学生答"就那个嘛"仍无明确功能名
- **THEN** 不二次澄清，直接按 default 进入链路

#### Scenario: 点选候选重发（权威锚定）
- **WHEN** 学生点选候选 chip（如 [RAG项目]），前端**重发原问题 + `current_project=rag-system`**（含 clarify 轮 history）
- **THEN** intent 以 `current_project` 为**权威消歧锚点**直接锚定 `anchor=rag-system`，**不因问题本身含糊再拉 ambiguous**
- **AND** 点选模块与会话锚点不同 → `switch` 事件照常触发

### switch 上下文切换（重置上下文）
> 状态：⚠️
> 检索摘要：学生切换功能时上下文怎么处理？intent switch_detected 触发 switch 事件携带新旧锚点，重置锚点/召回/轮次后按新锚点走链路。

系统 SHALL 在 intent 判定 `switch_detected=true` 时发出 `switch` 事件（`{from_anchor, to_anchor}`）并**重置上下文**（锚点/召回/轮次计数），随后按新锚点走 rewrite→recall→generate；不掐断任何在途流（在途流完成或被 is_disconnected 取消）。

#### Scenario: 切换功能
- **WHEN** 学生从 AI答疑 切到 RAG 项目提问（switch_detected=true）
- **THEN** 发 `switch` 事件 + 重置上下文 → 走新锚点链路

### is_quoted 确定性引用（LCS 硬匹配）
> 状态：⚠️
> 检索摘要：怎么判定回答真的引用了召回块？精排块与 answer 做 LCS 最长公共子串，连续 8 中文字符命中即 is_quoted，纯函数可入评估。

系统 SHALL 生成完成后对精排块 text/summary 与最终 answer 做 LCS 最长公共子串匹配，任意**连续 8 中文字符（或 12 英文字符）**命中 → is_quoted=true；done 后补发 `quotedKeys`。非 LLM 自述，纯函数可单测可入评估。

#### Scenario: 命中引用
- **WHEN** answer 含精排块原文连续 ≥8 中文字符
- **THEN** quotedKeys 含该块 blockId

#### Scenario: 改写未命中
- **WHEN** answer 全部改写、无连续 8 字命中
- **THEN** quotedKeys 不含该块（前端灰显兜底）

### 模块可用性数据驱动
> 状态：⚠️
> 检索摘要：模块语料后补会自动变可答吗？语料存在性决定模块可否答，无语料走低置信过滤，切片入库后自动可答无需改代码。

系统 SHALL 由语料存在性决定模块可否答：无语料模块正常进入召回但命中空/低置信 → 低置信过滤；未来语料入库切片 → 自动可答（无代码改动）。

#### Scenario: 语料后补自动可答
- **WHEN** RAG 模块语料切片入库后
- **THEN** 该模块提问从低置信拒答变为正常召回回答
