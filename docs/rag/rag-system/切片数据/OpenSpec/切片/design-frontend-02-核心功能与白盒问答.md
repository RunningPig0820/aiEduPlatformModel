# 核心功能与白盒问答
> summary: 核心功能与白盒问答（面板形态与白盒链路）
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-frontend-02-核心功能与白盒问答.md
> 类别：操作流程

---

> 检索摘要（业务向）：前端 RAG 助手面板怎么把"RAG 在动"白盒展示出来？面板改造目标/Goals 是什么？进入页面默认展开、收起留提示条、置顶头部、白盒流水线阶段（权限/意图/改写/召回/重排/生成）如何按 SSE 事件顺序渲染？

### Context
> 检索摘要：学生 RAG 项目介绍助手前端改造目标：把现有 AI 助手改成默认展开面板，白盒展示权限/意图/改写/召回/重排/生成全链路，让"RAG 在动"可见。

- 后端契约已冻结（`rag-project-intro-assistant`）：Java 网关角色门（仅 STUDENT）+ SSE 白盒事件中继；Python 白盒链路（intent/rewrite/recall/rerank/generate + clarify/is_quoted/分层超时/suggestions/tokens_usage）。
- 前端现状：`AIChatPanel` 右下角隐藏 FAB + 抽屉（默认收起），不展示链路；页面 `pageMeta` 已含 `intro`。
- 目标：把现有 AI 助手改造成学生 RAG 项目介绍助手——进入默认展开、收起留提示、置顶头部（当前页面 + 用户角色 + 消耗 token）、白盒流水线可视化、引用可点、成本透明、引导完整、澄清可点选。

### Goals / Non-Goals
> 检索摘要：Goals 明确白盒展示 RAG 链路、引用面板灰显高亮、成本面板、引导 chips、澄清点选；Non-Goals 明确不改后端、不改 AI答疑页交互、不做 mermaid 流程图。

**Goals**
- 白盒展示 RAG 链路全过程（权限/意图/改写/召回/重排/生成），按 SSE 事件顺序渲染
- 改造 AI 助手：默认展开、收起留提示条、置顶头部
- 引用面板（灰显 → quotedKeys 高亮）、成本面板（本轮 + 会话累计）、引导 chips、澄清点选
- 每次 ask 携带 `currentProject`（当前页面 → 模块锚点）
- 非学生占位说明；断线补查；会话结算
- 纯前端增量，零后端改动

**Non-Goals**
- 不做后端/模型端实现（契约已定）
- 不改现有 AI答疑（AiQa）自身交互（AI答疑页不挂 RAG 助手，避免双聊天混淆）
- 不做 mermaid 动态生成（后端 Non-Goal 同理，本期不做流程图渲染）
- 不做 /demo 三角色看板工作台（被本方案取代）

### D1: 变更组织
> 检索摘要：新增 add-rag-assistant-frontend 统一前端变更，替代原 add-demo-showcase-page 方向，pageMeta.intro 并入本方案复用。

新建 `add-rag-assistant-frontend`（统一前端变更，替代原 `add-demo-showcase-page` 方向）；`pageMeta.intro` 已并入本方案复用。原 `add-demo-showcase-page` 方案作废/归档。

### D2: 助手面板形态（改造 AIChatPanel）
> 检索摘要：把右下角 AIChatPanel 改造成 RagAssistantPanel：进入页面默认展开、收起留固定悬浮细条、置顶头部，排除 AI答疑页避免双聊天混淆。

将现有右下角 FAB 抽屉 `AIChatPanel` 改造为 **RagAssistantPanel**（或加 `mode="narrator"` 保持默认行为向后兼容）：

```
┌───────────────────────────────────────────────┐
│ 置顶头部: 当前页面 · 角色:学生 · 本场 Token:1,690 │  ← 固定, 不随滚动
├───────────────────────────────────────────────┤
│ 白盒流水线(每轮实时点亮)                       │
│  ①权限控制 ✓ STUDENT                        │
│  ②意图识别 ✓ 项目介绍 / anchor=ai-tutoring     │
│  ③Query改写 ✓ 原问→改写                      │
│  ④多路召回 ✓ 向量+BM25 → Top3                │
│  ⑤重排     ✓ RRF                            │
│  ⑥生成     ✓ token*                         │
│  (分支) clarify / switch / boundary           │
├───────────────────────────────────────────────┤
│ 引用面板: 块1✓已引用 | 块2(灰) | 块3·查看原文   │
├───────────────────────────────────────────────┤
│ 对话区: 用户 / AI 流式回答 / 结束建议chips      │
│ 开始引导 chips(GET /guide) · 结束对话按钮       │
└───────────────────────────────────────────────┘
```

- **进入页面默认展开**（不再隐藏 FAB）；**收起 → 固定悬浮细条**，始终显示一条当前建议"建议问问: …"（可点发送、可点展开）。
- 挂载：学生端 DashboardLayout 各页（与现有 AIChatPanel 相同位置），**排除 AI答疑页**（该页自带聊天，避免双聊天混淆）。

### D4: 白盒流水线可视化
> 检索摘要：新增 PipelineStages 按 SSE 事件顺序点亮阶段行，permission/intent/clarify/switch/rewrite/rerank/boundary/token/done 各对应渲染；分支渲染已在 F-M2 落地。

仿 `AgentWorkflowPanel`/`workflowStages.jsx` 的 StageRow 范式，新增 `PipelineStages.jsx`：每个 SSE 事件到达 → 对应阶段行点亮（✓/脉动/灰），事件顺序即链路顺序。

| 事件 | 阶段行 |
|---|---|
| permission | 权限控制：{role, allowed} |
| intent | 意图识别：anchor/category/ambiguous/degraded |
| clarify | 澄清分支（候选点选，见 D7） |
| switch | 切换分支：from→to（前端提示"已切换至 X"） |
| rewrite | Query 改写：原问 vs 改写 |
| rerank | 多路召回 + 重排：Top-K 块数 |
| boundary | 边界：reason=low_confidence，展示固定话术（非错误） |
| token/done | 生成：流式正文 + 完成 |

**分支渲染已在 F-M2 落地**：`clarify`（需澄清横幅 + ⑤待澄清阶段，③Query改写/④召回标记"已跳过"不再转圈）、`boundary`（边界拒答）、`switch`（已切换至 X）三分支均已渲染；`done` 到达终止一切转圈。clarify 的**交互 chips 点选**（见 D7）属 F-M6。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-frontend-rag-assistant-frontend.md`（§Context §Goals/Non-Goals §D1 §D2 §D4）
