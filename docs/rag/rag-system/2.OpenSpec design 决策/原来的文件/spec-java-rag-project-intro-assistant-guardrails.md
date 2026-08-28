# rag-assistant-guardrails Specification

## Purpose

模块全放行（AI答疑/知识图谱/题型分析/RAG 四模块无禁区）+ 范围门低置信度过滤（唯一拒答路径）、clarify 澄清轮、is_quoted 确定性引用硬匹配、模块可用性数据驱动（当前仅 AI答疑有语料，其余模块入库即自动可答）。

## ADDED Requirements

### Requirement: 模块全放行与硬路由

系统 SHALL 放行 AI答疑/知识图谱/题型分析/RAG 四个模块的提问（**无禁区模块**），intent 将问题路由到对应模块知识库。凡问题涉及"系统架构/代码实现/部署流程/评测方案/接口设计"，强制路由至 RAG 项目知识库。模块是否有可答内容由语料决定，**不在意图层硬拒答任何模块**——查不到关联文档由范围门低置信度过滤处理。

#### Scenario: 四模块放行

- **WHEN** 学生问题指向 AI答疑/知识图谱/题型分析/RAG 任一模块
- **THEN** intent 路由到对应模块，进入召回流程，意图层不拒答任何模块

#### Scenario: 涉及架构路由至 RAG 项目

- **WHEN** 问题涉及"系统架构/代码实现/部署流程/评测方案/接口设计"
- **THEN** intent 强制路由至 RAG 项目知识库，正常进入召回流程

### Requirement: 范围门低置信度过滤（唯一拒答路径）

系统 SHALL 在召回精排后判定综合分是否低于阈值（索引层 0.75 / 源文档池 0.5，沿用）；低于 → 返回固定话术"未找到关联文档，我尚未掌握"，事件为 `boundary`（reason=low_confidence），该路径已消耗 recall token 但**不调用 generate**。此为本助手唯一拒答路径——无禁区模块硬拒答，所有拒答均由低置信度触发。

#### Scenario: 无语料模块低置信过滤

- **WHEN** 学生问及知识图谱模块且其无切片语料（语料命中为空/低置信）
- **THEN** 系统返回固定低置信话术，事件 `boundary` + reason=low_confidence，无生成 token

#### Scenario: 语料未覆盖的边角问题

- **WHEN** 语料存在但综合分低于阈值
- **THEN** 系统返回固定低置信话术，事件 `boundary` + reason=low_confidence，无生成 token

### Requirement: 固定话术不调 LLM

系统 SHALL 将拒答话术（范围门低置信/超时降级）写死，严禁调用 LLM 生成拒答语，保证 0 token 成本。

#### Scenario: 拒答零成本

- **WHEN** 任一拒答分支触发
- **THEN** 返回写死话术，不产生 LLM 调用，tokens_usage 均为 0

### Requirement: clarify 澄清轮

系统 SHALL 在 intent 判定 `ambiguous=true` 且候选功能 ≥2 时发出 `clarify` 事件（固定话术模板 + candidates + default），不进入召回与生成、0 token、**不计入答案轮次**，并写入历史；学生下一条消息重跑 intent。若下一条仍模糊，**不再二次澄清**，直接默认当前功能继续。**候选判定输入**：`candidates` = ① intent LLM 结构化输出直接给出（`ambiguous=true` 时输出候选模块闭集 2~4 个，主源）→ ② LLM 未给/给 <2 → 会话最近 N 轮锚过的模块去重填充（兜底）→ ③ 仍 <2 → 不触发 clarify 直接默认。`default` = 前端 `current_project` > 会话最后成功锚定功能。

#### Scenario: 多候选澄清

- **WHEN** 学生问"这个功能的流转是什么样的"，intent LLM 判定 ambiguous 并输出 `candidates:["ai-tutoring","rag-system"]`（或会话历史锚点兜底 ≥2）
- **THEN** 系统发 `clarify` 事件（如"您的问题涉及多个功能，请明确功能名。默认回答当前功能：AI答疑" + candidates + default=AI答疑，default 绑定 current_project），无 recall/generate

#### Scenario: 点选候选重发

- **WHEN** 学生点选候选 chip（如 [RAG项目]），前端重发 **原问题 + current_project=rag-system**（含 clarify 轮 history）
- **THEN** intent 以 current_project 为权威消歧锚点直接锚定 `anchor=rag-system`，不再 ambiguous；若与会话锚点不同则 `switch` 事件照常触发，随后正常 rewrite/recall/generate

#### Scenario: 澄清一次后仍模糊

- **WHEN** 学生回答"就那个嘛"（仍无明确功能名）
- **THEN** 系统不二次澄清，直接按 `default`（当前功能）进入正常链路

#### Scenario: 单一候选不澄清

- **WHEN** 问题模糊但会话内只讨论过一个功能
- **THEN** 系统不触发澄清，直接按当前功能默认回答（低摩擦）

#### Scenario: 问候语不澄清（欢迎引导）

- **WHEN** 学生发"你好"等问候语（intent 判 category=问候、ambiguous=false）
- **THEN** 系统不触发 clarify，直接返回固定欢迎话术 + 引导建议（指向 ①项目介绍②操作③数据关联④难点，复用 guide 静态池），0 生成 token、不 recall 不 generate

### Requirement: is_quoted 确定性硬匹配

系统 SHALL 在生成完成后，对精排 Top-K 块的 `text`/`summary` 与最终 answer 做最长公共子串匹配：任意**连续 8 个中文字符（或 12 个英文字符）**命中即标记该块 `is_quoted=true`。该判定为确定性硬匹配，**不依赖 LLM 自述**。前端 `rerank` 先展示全部块，`done` 后以 `quotedKeys` 补发命中集合（未命中灰显折叠）。

#### Scenario: 命中引用

- **WHEN** answer 中包含某块的连续 8 个中文字符片段
- **THEN** 该块 `is_quoted=true`，进入 `done.quotedKeys`

#### Scenario: 未命中

- **WHEN** answer 与某块无任何 ≥8 中文字符连续命中
- **THEN** 该块 `is_quoted=false`，前端灰显折叠，不视为引用依据

#### Scenario: 全部未命中

- **WHEN** top-K 块全部未命中
- **THEN** answer 标注"基于现有知识库，引用未能精确匹配"，quotedKeys 为空，不假装存在引用

### Requirement: 模块可用性数据驱动

系统 SHALL 按语料实际存在与否决定模块是否可答：存在切片语料的模块可正常召回并回答；尚无语料的模块**正常进入召回**，但命中为空/低置信 → 范围门低置信度过滤（固定话术）。模块可用性不得硬编码，未来某模块入库切片后自动可答（无需改代码）。

#### Scenario: 无语料模块低置信过滤

- **WHEN** 学生问及知识图谱模块且其无切片语料
- **THEN** 系统正常召回，命中为空/低置信 → `boundary` + reason=low_confidence，返回固定话术

#### Scenario: 入库后自动可答

- **WHEN** 知识图谱模块语料切片入库
- **THEN** 系统无需改代码自动识别该模块可答，正常召回并回答

### Requirement: 问题提示（开始引导 + 结束建议，RAG 常驻）

系统 SHALL 提供问题提示，且 **RAG 始终带上**（RAG 是始终在底层运行的引擎，非展示页模块，不能当四个并列模块之一）：
- **开始引导**：会话入口（未提问前）SHALL 展示 RAG 定向引导（定位/架构/数据流/评测/坑），静态池、0 token，走非 SSE 接口 `GET /api/rag/assistant/guide`，不占冻结的 SSE 时序。
- **结束建议**：每轮完成后 `done.suggestions` SHALL 返回 1~3 条建议（向 ①项目介绍 ②操作 ③数据关联 ④难点），且 **必含 ≥1 条 RAG 方向**（无论学生问哪个模块，都把话题带回 RAG）。LLM 失败 → 静态池兜底（对齐 Python 6 引导方向）。

#### Scenario: 开始引导定向 RAG

- **WHEN** 学生进入助手页/会话开始（未提问）
- **THEN** 前端展示 RAG 定向引导 chips（定位/架构/数据流/评测/坑），0 token、非 SSE 拉取

#### Scenario: 结束建议必含 RAG

- **WHEN** 学生问 AI答疑 模块完成一轮
- **THEN** `done.suggestions` 1~3 条中至少 1 条指向 RAG 方向

#### Scenario: 静态池兜底

- **WHEN** suggestions LLM 调用失败
- **THEN** 返回静态池预写建议（对齐 Python 6 引导方向），链路不中断

### Requirement: 切换上下文（switch 事件）

系统 SHALL 在下一轮 intent 判定 `switch_detected=true`（前端 current_project ≠ 会话已锚定 project，或问题明确指向另一有语料模块）时发出 `switch` 事件并重置上下文（锚点/召回/轮次计数），按新锚点继续 rewrite→recall→generate。**不做生成中切换**——在途流要么完成、要么由断连取消处理。

#### Scenario: 下一轮切换

- **WHEN** 学生上一轮在 AI答疑，下一轮问 RAG 架构
- **THEN** intent 判定 switch_detected=true，发 `switch` 事件（from/to），重置上下文后按 RAG 项目锚点继续

#### Scenario: 生成中不掐流

- **WHEN** 学生在前一轮生成过程中发起新问题
- **THEN** 系统不主动掐断在途流；新问题按下一轮处理（或由前端取消原 fetch）
