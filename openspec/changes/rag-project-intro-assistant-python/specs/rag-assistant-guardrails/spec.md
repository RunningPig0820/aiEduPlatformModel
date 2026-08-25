# rag-assistant-guardrails Specification

## Purpose

模块全放行（AI答疑/RAG/题型/知识图谱无禁区，语料驱动）+ 范围门低置信度过滤（唯一拒答路径）+ clarify 澄清轮 + is_quoted 确定性引用硬匹配。

## ADDED Requirements

### Requirement: 模块全放行与硬路由

系统 SHALL 放行 AI答疑/RAG/题型/知识图谱四模块提问（无禁区），intent 路由到对应模块语料池；问题涉及"系统架构/代码实现/部署流程/评测方案/接口设计" → 强制路由 RAG 项目知识库。模块可否答由语料决定，意图层不硬拒答任何模块。

#### Scenario: 四模块放行
- **WHEN** 学生问 AI答疑/RAG/题型/知识图谱任一模块
- **THEN** intent 路由对应模块，进入召回；意图层不拒答任何模块

#### Scenario: 涉及架构路由至 RAG
- **WHEN** 问题涉及"系统架构/代码实现/部署流程/评测方案/接口设计"
- **THEN** intent 强制路由 RAG 项目知识库

### Requirement: 范围门低置信度过滤（唯一拒答路径）

系统 SHALL 在精排后判定综合分是否低于阈值（索引层 0.75 / 源 0.5）；低于 → 固定话术"未找到关联文档，我尚未掌握"，`boundary` 事件（reason=low_confidence），消耗 recall token 但**不调 generate**。此为本助手唯一拒答路径（无禁区硬拒答）。

#### Scenario: 无语料模块低置信
- **WHEN** 问知识图谱且其无切片语料（命中空/低置信）
- **THEN** `boundary` + low_confidence 固定话术，无生成 token

#### Scenario: 语料未覆盖边角问题
- **WHEN** 语料存在但综合分低于阈值
- **THEN** `boundary` + low_confidence 固定话术，无生成 token

### Requirement: 固定话术不调 LLM

系统 SHALL 将拒答/超时降级话术写死，严禁调 LLM 生成，保证 0 token。

#### Scenario: 拒答零成本
- **WHEN** 任一拒答分支触发
- **THEN** 写死话术，tokens_usage 全 0

### Requirement: clarify 澄清轮

系统 SHALL 在 intent `ambiguous=true` 且 candidates ≥2 时发 `clarify` 事件（固定话术 + candidates + default），不 recall/generate、0 token、不计答案轮次、写 history；下一条重跑 intent；仍模糊不再二次澄清，直接默认当前功能。

候选判定（C4 定稿）：主源 = intent LLM `candidates`（2~4 个模块闭集）；LLM 未给/给<2 → 会话最近 N 轮锚过模块去重兜底；仍 <2 → 不触发 clarify。default = current_project > 会话最后锚定。

#### Scenario: 多候选澄清
- **WHEN** 问"这个功能的流转"且会话内多功能候选
- **THEN** `clarify`（"您的问题涉及多个功能，请明确功能名。默认回答当前功能：RAG项目" + candidates + default）

#### Scenario: 澄清一次后仍模糊
- **WHEN** 学生答"就那个嘛"仍无明确功能名
- **THEN** 不二次澄清，直接按 default 进入链路

### Requirement: switch 上下文切换（重置上下文）

系统 SHALL 在 intent 判定 `switch_detected=true` 时发出 `switch` 事件（`{from_anchor, to_anchor}`）并**重置上下文**（锚点/召回/轮次计数），随后按新锚点走 rewrite→recall→generate；不掐断任何在途流（在途流完成或被 is_disconnected 取消）。

#### Scenario: 切换功能
- **WHEN** 学生从 AI答疑 切到 RAG 项目提问（switch_detected=true）
- **THEN** 发 `switch` 事件 + 重置上下文 → 走新锚点链路

### Requirement: is_quoted 确定性引用（LCS 硬匹配）

系统 SHALL 生成完成后对精排块 text/summary 与最终 answer 做 LCS 最长公共子串匹配，任意**连续 8 中文字符（或 12 英文字符）**命中 → is_quoted=true；done 后补发 `quotedKeys`。非 LLM 自述，纯函数可单测可入评估。

#### Scenario: 命中引用
- **WHEN** answer 含精排块原文连续 ≥8 中文字符
- **THEN** quotedKeys 含该块 blockId

#### Scenario: 改写未命中
- **WHEN** answer 全部改写、无连续 8 字命中
- **THEN** quotedKeys 不含该块（前端灰显兜底）

### Requirement: 模块可用性数据驱动

系统 SHALL 由语料存在性决定模块可否答：无语料模块正常进入召回但命中空/低置信 → 低置信过滤；未来语料入库切片 → 自动可答（无代码改动）。

#### Scenario: 语料后补自动可答
- **WHEN** RAG 模块语料切片入库后
- **THEN** 该模块提问从低置信拒答变为正常召回回答
