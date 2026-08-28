## Why

后端已定契约（`rag-project-intro-assistant`，Java 网关 + Python 白盒链路）：学生侧需要一个能**证明 RAG 能力**、又能**讲清本项目设计逻辑**的白盒问答助手。后端把 RAG 标准链路中间状态（权限 → 意图 → 改写 → 多路召回 → 重排 → 生成）通过 SSE **实时透传**，回答带可点击的召回原文，并返回每轮/会话的 token 消耗。前端要把这套契约**可视化成面向学生的介绍助手**：白盒阶段看得见、引用可点、成本透明、引导完整。

现状：现有 `AIChatPanel` 是右下角隐藏 FAB + 抽屉，默认收起，不展示任何链路信息；页面 `pageMeta` 已含 `intro`（一句话解说词，已加）。

## What Changes

- **改造现有 AI 助手 → 学生 RAG 项目介绍助手**：学生进入页面**默认展开**（不再隐藏 FAB），收起时**留提示条**；置顶固定头部展示 `当前页面(pageMeta)` + `用户角色` + `消耗 token`。
- **白盒 RAG 流水线可视化**：消费后端 SSE 事件流（`permission → intent → (clarify|switch) → rewrite → rerank → (boundary) → token* → done`），按事件顺序渲染阶段卡——权限✓/意图识别/Query 改写/多路召回/重排/生成。
- **引用面板**：`rerank` 块先灰显（标题/摘要/原文 filePath 可点），`done` 后 `quotedKeys` 命中的高亮展开、未命中折叠。
- **成本面板**：`done.tokensUsage` 四字段（prompt/completion/cacheHit/total）+ `close` 返回的会话累计 token。
- **引导完整**：进入拉 `GET /guide` 展示 RAG 定向开始引导 chips；每轮 `done.suggestions` 渲染结束建议 chips（点击→重发原问重走链路，必含 RAG）。
- **澄清交互**：`clarify` 事件渲染候选 chips，点选候选 = **重发原问 + `currentProject`=点选模块**（契约已冻结，两端已落盘）。
- **页面→模块锚点**：每次 ask 携带 `currentProject`（由当前页面 pageMeta 映射），告知后端语料池。
- **非学生处理**：面板显示当前角色，非学生 → 展示"当前非学生无法使用"占位（后端仍 403 兜底）。
- **断线补查**：SSE 中断后凭 `trace_id` 调 `GET /turns/{traceId}` 补查该轮。

## Capabilities

### New Capabilities
- `rag-assistant-ui`: 学生 RAG 项目介绍助手前端——默认展开面板、白盒流水线可视化、引用面板、成本面板、引导/澄清交互、非学生占位、会话结算与断线补查

### Modified Capabilities
- `ai-chat-panel`: 现有 AI 助手改造为 RAG 助手（默认展开/收起留提示、置顶头部）
- `page-meta`: `intro` 字段已加；新增"页面 → 模块锚点"映射配置供 `currentProject`

## Impact

- **新增文件**：
  - `src/api/modules/ragAssistant.js` — ragApi（ask SSE/非流式、close、turns、guide、eval/report）
  - `src/utils/ragSse.js` — SSE 事件分发 client（permission/intent/clarify/switch/rewrite/rerank/boundary/token/done）
  - `src/components/rag-assistant/RagAssistantPanel.jsx` — 助手面板主体（默认展开/收起留提示/置顶头部）
  - `src/components/rag-assistant/PipelineStages.jsx` — 白盒阶段可视化（仿 `AgentWorkflowPanel` StageRow）
  - `src/components/rag-assistant/ReferencePanel.jsx` — 引用面板（灰显→高亮）
  - `src/components/rag-assistant/CostBar.jsx` — 成本展示（本轮 + 会话累计）
  - `src/components/rag-assistant/GuideChips.jsx` — 开始/结束引导 chips
  - `src/components/rag-assistant/ClarifyCard.jsx` — 澄清候选点选
  - `src/constants/pageModuleMap.js` — 页面 pageCode → currentProject 模块锚点映射
- **修改文件**：
  - `src/components/common/AIChatPanel.jsx`（或替换为 RagAssistantPanel）— 默认展开、收起留提示、置顶头部、消费 RAG 契约
  - `src/constants/pageMeta.js` — `intro` 已加（本变更引用）
  - `src/routes.jsx` — 学生页传递 pageCode（若需）/ 挂载助手
- **复用不改**：`AgentWorkflowPanel` 阶段渲染范式、AiQa 消息/Markdown 渲染、`llmApi` SSE 读取模式
- **后端**：零改动（消费既有契约）；非学生后端固定 403，前端做占位说明

## 对齐说明（与后端契约的同步点）

- 后端 M1–M8 里程碑已冻结契约；本变更任务按 **F-M1~F-M8** 与后端里程碑纵向对齐，每里程碑可联调（后端桩替期前端先渲染）。
- 澄清点选交互（点选候选 = 重发原问 + currentProject）已在后端 design/spec/api/test 与 Python design/spec/test 落盘。
