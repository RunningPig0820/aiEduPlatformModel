# milestone-06-suggestions Specification

## Purpose

M6 交付"问题提示"切片（原清单 #2）——**开始引导 + 结束建议 + clarify 澄清追问**。RAG 是特殊模块：**不是展示页（学生无法导航到），而是始终在底层运行的引擎**，每轮答案都由它产出，所以问题提示**每次必须带上 RAG**。开始引导（会话入口，静态池定向 RAG）、结束建议（done 后，1~3 条且必含 RAG 方向）、clarify（歧义先问清）。前端以引导 chips + 澄清追问 UI 验收。本切片是原清单"问题提示"依赖序修正的落点（在 done 之后，故排 M6）。

## ADDED Requirements

### Requirement: 开始引导定向 RAG（非 SSE）

M6 SHALL 交付会话入口引导：学生进入助手页（未提问前）SHALL 看到 RAG 定向引导（定位/架构/数据流/评测/坑），静态池、0 token，走非 SSE 接口 `GET /api/rag/assistant/guide`，**不占冻结的 SSE 时序**。会话开始无上下文，LLM 无从生成，静态池即最优。

#### Scenario: 进入助手展示开始引导

- **WHEN** 学生进入助手页/会话开始（未提问）
- **THEN** 前端拉取 guide 池并展示 RAG 定向引导 chips，0 token

#### Scenario: 不占 SSE 时序

- **WHEN** 开始引导展示时发起第一问
- **THEN** SSE 时序仍为 `permission → intent → ...`，guide 为独立非 SSE 调用，不影响冻结契约

### Requirement: 结束建议必含 RAG 方向

M6 SHALL 交付结束后建议：每轮 done 后调 LLM 生成 1~3 条建议（向 ①项目介绍 ②操作 ③数据关联 ④难点 引导），**必含 ≥1 条 RAG 方向**——无论学生问哪个模块（AI答疑/知识图谱/题型分析），答案都是 RAG 引擎产出的，必须把话题带回 RAG。completion_tokens 计入本轮 usage；LLM 失败 → 静态池兜底（对齐 Python 侧 6 引导方向：定位/架构/数据流/防作弊/评测/坑），RAG 方向常驻，保证不挂。

#### Scenario: 引导 chips 展示

- **WHEN** 一轮生成完成
- **THEN** done 携带 suggestions（1~3 条），前端渲染为可点击引导 chips

#### Scenario: 建议必含 RAG

- **WHEN** 学生问 AI答疑 模块完成一轮
- **THEN** done.suggestions 中至少 1 条指向 RAG 方向（RAG 始终带上，非并列模块）

#### Scenario: 静态池兜底

- **WHEN** suggestions LLM 调用失败
- **THEN** 返回静态池预写建议（含 RAG 方向，对齐 Python 6 引导方向），链路不中断

### Requirement: clarify 澄清追问

M6 SHALL 交付歧义澄清：`ambiguous=true` 且 candidates ≥ 2 → `clarify` 事件（固定话术 + candidates + default），0 生成 token、不计答案轮次、写 history；最多一轮，再模糊直接默认当前功能继续；`default` 绑定优先级：前端 `current_project` > 会话最后成功锚定功能。**候选来源**：① intent LLM 输出 candidates（主源）→ ② 会话最近 N 轮锚点去重（兜底）→ ③ 仍 <2 不触发澄清直接默认。**点选交互定稿**：点选候选 chip → 前端重发原问题 + `current_project=点选模块`（含 clarify 轮 history），intent 以 current_project 为权威消歧锚点直接锚定，不再 ambiguous；点选锚点与会话锚点不同则 switch 事件照常。

#### Scenario: 澄清追问触发

- **WHEN** 问题歧义（如"这个功能的流转是什么样的"跨功能）
- **THEN** intent 后 clarify 事件（message/candidates/default），无 recall/generate，随后 done

#### Scenario: 澄清后仍模糊

- **WHEN** 澄清一轮后学生仍不明确
- **THEN** 不再澄清，默认当前功能继续，防死循环

### Requirement: 问候识别与欢迎引导

M6 SHALL 交付问候处理：intent 识别问候/寒暄（如"你好"）为 `category=问候`、`ambiguous=false`，**不触发 clarify**（clarify 仅用于功能指代不明，不用于问候语）；问候语直接返回**固定欢迎话术 + 引导建议**（指向 ①项目介绍②操作③数据关联④难点，复用 guide 静态池），0 生成 token、不 recall 不 generate。

#### Scenario: 问候语欢迎引导

- **WHEN** 学生发"你好"
- **THEN** intent 判 category=问候/ambiguous=false，不 clarify；done 直接返回欢迎话术 + 引导建议，0 生成 token

### Requirement: 里程碑对接测试验收

M6 SHALL 以引导 + 澄清用例作为完成标准：RAG-SSE-004（clarify 时序）、RAG-SSE-005（switch 时序，依赖 M2 已交付的 switch）、suggestions 展示用例。

#### Scenario: 对接测试全绿

- **WHEN** 前端完成引导 chips 与澄清追问 UI 对接
- **THEN** RAG-SSE-004/005、suggestions 展示用例通过，M6 视为完成

#### Scenario: 前端可见物

- **WHEN** 一轮生成完成
- **THEN** 前端渲染引导 chips；歧义问题时弹出澄清追问（默认当前功能）
