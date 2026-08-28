# milestone-02-intent-sse Specification

## Purpose

M2 交付"白盒骨架 + 意图分析 + Query 改写"切片——SSE 事件通道、事件时序冻结、trace_id、intent LLM 结构化输出、rewrite 透传、switch 判定。本切片搭建整条链的"阶段展示"基础设施，generate 以桩替占位，使整轮可通、前端可对阶段区做对接。**SSE 事件契约在本切片定稿，后续里程碑只补字段不重排。**

## ADDED Requirements

### Requirement: SSE 白盒事件通道与时序冻结

M2 SHALL 搭建 SSE 事件通道并冻结时序 `permission → intent → (clarify|switch) → rewrite → rerank → (boundary) → token* → done`。前端可订阅各阶段事件并展示中间状态；字段命名 camelCase，沿用 `FAIL_ON_UNKNOWN_PROPERTIES=false` 容忍未知字段。generate 未实现期间以固定桩替占位答案回填 `done`，保证整轮可通。**归属（定死）**：`permission` 仅 Java 网关产出（角色门在 Java），**携带 `traceId`（Java 入口生成，前端流开始即可取，供断线补查不依赖 done）**；Python API 从 `intent` 开始，桥从 intent 转发不消费 Python 侧 permission；`history`（最近 N 轮含 clarify 轮）+ `trace_id`（Java 生成）随 ask 请求传 Python，Python done 回显。

#### Scenario: 阶段时序展示

- **WHEN** 学生发起一问（M2 阶段，generate 为桩替）
- **THEN** 前端依次收到 permission → intent → rewrite → done，阶段展示区可看到"权限✓ / 意图分类标签 / 改写后问题 / 桩替答案"

#### Scenario: 契约冻结

- **WHEN** 后续里程碑（M3-M7）新增事件字段
- **THEN** 只向既有事件追加字段，不得重排事件顺序、不得删除已发布字段

#### Scenario: permission 仅 Java

- **WHEN** Java 桥中继 Python SSE 流
- **THEN** 桥从 Python 的 `intent` 事件开始转发，不消费/不透传 Python 侧任何 permission（permission 由 Java 在调用桥前已发）

### Requirement: intent 结构化输出与规则兜底

M2 SHALL 交付 intent 语义分析：LLM 结构化输出 `{anchor, category, switch_detected, ambiguous, candidates}`；失败/超时/非闭集 → 回退关键词锚定（复用 `_fallback_anchor`），degraded 标记走 200 不报错。前端展示意图分类标签与路由目标。**两层锚定**：`anchor`=模块级（路由层，选语料池），`lockedSections`=节级（加权层，池内精化），两层并存，orchestrate 节级锚定逻辑保留仅加选池。**candidates**：ambiguous 时 LLM 输出候选模块闭集（主源），会话最近 N 轮锚点兜底。

#### Scenario: 意图分类展示

- **WHEN** 学生提问指向某模块
- **THEN** intent 事件携带 anchor/category，前端展示分类标签（如 #ai_tutoring / #rag_project）

#### Scenario: 歧义输出候选

- **WHEN** 学生问题"这个功能的流转是什么样的"（跨功能指代不明）
- **THEN** intent 输出 ambiguous=true 及 candidates（如 ["ai-tutoring","rag-system"]，闭集见设计 D-A），供 M6 clarify 判定

#### Scenario: LLM 失败兜底

- **WHEN** intent LLM 调用失败
- **THEN** 回退关键词锚定，degraded=true 走 200，链路不中断

### Requirement: Query 改写透传

M2 SHALL 交付 rewrite 阶段：生成改写后 query 并透传 `rewrite` 事件，前端展示"原始问题 → 改写后问题"。

#### Scenario: 改写展示

- **WHEN** 学生提交问题
- **THEN** rewrite 事件携带改写后 query，前端展示改写前后对照

### Requirement: switch 判定与事件

M2 SHALL 交付切换判定：`switch_detected = (前端 current_project ≠ 会话锚定 project) 或 (问题明确指向另一有语料模块)`，检测到发 `switch` 事件（from/to）。切换收敛在下一轮 intent，不做生成中切换。

#### Scenario: 跨功能切换

- **WHEN** 学生在 AI答疑页切换话题到 RAG 项目
- **THEN** switch 事件（from=ai_tutoring, to=rag_project）后按新锚点 continue rewrite→recall→generate

### Requirement: 里程碑对接测试验收

M2 SHALL 以桩替链路跑通 + 时序/契约用例作为完成标准：RAG-SSE-001（桩）、RAG-CONTRACT-002（snake↔camel）、RAG-CONTRACT-003（未知字段容忍）、RAG-COST-003（trace 贯穿）。generate 桩替移除需等 M4。

#### Scenario: 对接测试全绿

- **WHEN** 前端完成阶段展示区对接，后端桥 mock 桩替流
- **THEN** RAG-SSE-001（桩）/RAG-CONTRACT-002/003/RAG-COST-003 通过，M2 视为完成

#### Scenario: 前端可见物

- **WHEN** 学生发起一问
- **THEN** 前端阶段展示区实时呈现 权限✓ → 意图分类 → 改写后问题，整轮以桩替答案收尾
