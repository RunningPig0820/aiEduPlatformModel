> summary: 本设计定义学生 RAG 项目介绍助手前端改造方案：把现有 AI 助手改造成默认展开面板，白盒展示 RAG 链路（权限/意图/改写/召回/重排/生成），支持引用面板灰显高亮、token 成本透明、引导 chips、澄清点选、非学生占位与断线补查，纯前端增量零后端改动。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-source/rag-system/OpenSpec设计决策/design-frontend-rag-assistant-frontend.md
> 类别：操作流程

# Design: 学生 RAG 项目介绍助手前端

## 文档说明
> 本文件为原始spec文档的RAG结构化重构版本。
> ⚠️重要提示：本文属于**设计阶段素材**，同时包含✅已落地、⚠️构想未实现、❓待决策内容；业务真实实现请以权威度0.8的canonical真相源文档为准。本文件独立完整，内容不拆分到外部canonical文档。

### Context
> 状态：⚠️
> 检索摘要：学生 RAG 项目介绍助手前端改造目标：把现有 AI 助手改成默认展开面板，白盒展示权限/意图/改写/召回/重排/生成全链路，让"RAG 在动"可见。

- 后端契约已冻结（`rag-project-intro-assistant`）：Java 网关角色门（仅 STUDENT）+ SSE 白盒事件中继；Python 白盒链路（intent/rewrite/recall/rerank/generate + clarify/is_quoted/分层超时/suggestions/tokens_usage）。
- 前端现状：`AIChatPanel` 右下角隐藏 FAB + 抽屉（默认收起），不展示链路；页面 `pageMeta` 已含 `intro`。
- 目标：把现有 AI 助手改造成学生 RAG 项目介绍助手——进入默认展开、收起留提示、置顶头部（当前页面 + 用户角色 + 消耗 token）、白盒流水线可视化、引用可点、成本透明、引导完整、澄清可点选。

### Goals / Non-Goals
> 状态：⚠️
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
> 状态：⚠️
> 检索摘要：新增 add-rag-assistant-frontend 统一前端变更，替代原 add-demo-showcase-page 方向，pageMeta.intro 并入本方案复用。

新建 `add-rag-assistant-frontend`（统一前端变更，替代原 `add-demo-showcase-page` 方向）；`pageMeta.intro` 已并入本方案复用。原 `add-demo-showcase-page` 方案作废/归档。

### D2: 助手面板形态（改造 AIChatPanel）
> 状态：⚠️
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

### D3: currentProject 来源（页面 → 模块锚点，定稿 4 id 闭集）
> 状态：⚠️
> 检索摘要：每次 ask 携带 currentProject 模块 id（页面 pageCode 映射），模块 id 闭集定稿：ai-tutoring/knowledge-graph/question-analysis/rag-system，clarify 候选为字符串 id 数组。

每次 `ask` 携带 `currentProject`（camelCase），由 **当前页面 pageCode → 模块 id** 映射（`src/constants/pageModuleMap.js`）。模块 id 闭集三端定稿（**rag-system，弃 rag-project；question-analysis，弃 question-type**）：

| 模块 id | 业务模块 | 语料 |
|---|---|---|
| ai-tutoring | AI答疑 | 已有 234 块 ✅ |
| knowledge-graph | 知识图谱 | 未切片 |
| question-analysis | 题型分析 | 未切片 |
| rag-system | RAG 项目 | 未切片（9 节待跑） |

页面映射（pageCode → id）：STUDENT_AI_QA→ai-tutoring（**保留**，供后续 AI答疑页挂面板）/ STUDENT_KNOWLEDGE_GRAPH·STUDENT_REPORT_MAP→knowledge-graph / 题型掌握·题型分析→question-analysis / 缺省→rag-system（全局）。

`pageModuleMap` 同时维护 **id→中文 label**：clarify `candidates` 为**字符串 id 数组**，前端渲染候选 chips 用 label；点选以 **id** 作为 `currentProject` 重发；**未知 id 显示原文兜底**。

### D4: 白盒流水线可视化
> 状态：✅
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

### D5: 引用面板（灰显 → 高亮）
> 状态：⚠️
> 检索摘要：rerank 到达即渲染引用块卡片灰显折叠，done 后 quotedKeys 命中块高亮展开，filePath 可点查看原文（GET source?path= 用 query 传参）。

`rerank` 事件到达即渲染块卡片（blockId/title/summary/filePath，**灰显折叠**，filePath 可点"查看原文"）；`done` 后 `quotedKeys` 命中的块**高亮展开**、未命中保持灰显折叠。`quotedKeys` 为空 → 展示 answer 自带标注，不额外提示。

**"查看原文" URL 定稿**：`GET /api/rag/assistant/source?path=<urlencoded>`（Java 网关代理透传 Python，STUDENT 角色门）。前端**拼 query 传参，不走 path**（file_path 含 `http://` 前缀，走 path 会被容器拒）。

### D6: 成本面板（本轮 + 会话累计）
> 状态：⚠️
> 检索摘要：置顶头部展示本场累计 token，done.tokensUsage 到达即更新；"结束对话"调 close 接口返回会话累计 token 与轮数。

- 置顶头部展示**本场累计 token**；每轮 `done.tokensUsage` 到后更新（`cacheHitTokens` 为估算值时标注"估算"）。
- "结束对话"调 `POST /sessions/{sessionId}/close`，返回会话累计 token + 轮数 → 展示"本次对话总消耗"。

### D7: 澄清交互（点选候选 → 重发原问 + currentProject）
> 状态：⚠️
> 检索摘要：clarify 事件渲染 ClarifyCard，candidates 为字符串 id 数组，点选候选=重发原问+currentProject=点选模块 id，后端以 currentProject 权威锚定。

`clarify` 事件到达 → 渲染 ClarifyCard：固定话术 + 候选 chips + default 提示。**candidates 为字符串 id 数组**（如 `["ai-tutoring","rag-system"]`）；前端用 `pageModuleMap` 的 id→中文 label 渲染 chips（未知 id 显示原文兜底）。**点选候选 = 重发原问 + `currentProject`=点选模块 id**（契约已冻结，**不是发裸功能名**）。后端 intent 以 currentProject 为权威锚点直接锚定；点选模块与会话锚点不同 → `switch` 事件照常触发（前端提示"已切换至 X"）。

### D8: 非学生占位
> 状态：⚠️
> 检索摘要：面板读取 auth 角色置顶展示，非 STUDENT 显示"当前非学生无法使用"占位，不发起 ask、不弹走页面，后端 403 兜底。

面板读取 auth 角色置顶展示；角色非 STUDENT → 面板内显示"**当前非学生无法使用**"占位，不发起 ask（后端 403 兜底）。不弹走页面、不硬报错。

### D9: SSE client 与断线补查
> 状态：⚠️
> 检索摘要：ragSse.js 读取 SSE 流按事件类型分发；permission 事件携带 traceId 流开始即存；断线用 traceId 调 turns 接口补查，trace 过期提示重发。

`src/utils/ragSse.js`：读取 `POST /api/rag/assistant/ask`（`stream:true`）SSE 流，按 event 类型分发（permission/intent/clarify/switch/rewrite/rerank/boundary/token/done），解析 camelCase 契约字段。

- **traceId 获取时机（定稿）**：`permission` 事件携带 `traceId`（`{role, allowed, traceId}`），前端**流开始即存**本轮 traceId——任意阶段断连都能补查；`done` 回显做一致性校验。
- **sessionId（定稿）**：前端**面板挂载时用 `llmApi.generateSessionId()` 生成 UUID**，整场会话复用；Java 以 sessionId 为键累计，ask 未知 session 按新会话。
- **ask 请求字段 camelCase**：`currentProject` / `question` / `sessionId` / `history` / `traceId` / `stream` / `topK`。
- **断线补查**：SSE 中断 → 用已存 traceId 调 `GET /api/rag/assistant/turns/{traceId}` 补查该轮；trace 过期（10002）→ 提示重发。

### D10: 轮次防卡死（分支终止 + 超时自关闭）
> 状态：⚠️
> 检索摘要：done 是所有分支终止点，到达即停全部转圈并定稿；单轮 45s 超时前端主动取消本轮提示重试，防止无限转圈。

SSE 不是纯线性链路——`clarify`/`boundary`/`switch` 三个分支各有对应渲染，且 **`done` 是所有分支的终止点**：不管本轮走正常链路还是澄清/边界/切换，done（或 error）到达必须停掉所有"处理中"转圈、阶段区定稿。clarify 轮 done 带空 answer → 气泡回显 `clarify.message`，不空白。

**超时兜底（定稿）**：单轮 45s（后端桥 60s 超时的前端兜底）未收到 done/error → 前端主动取消本轮，提示"响应超时，已结束本轮，请重试"，恢复可输入。防止任何分支/后端异常导致无限转圈。

### D11: 按页会话（换页独立刷新，演示定稿）
> 状态：⚠️
> 检索摘要：面板按 pageCode 重挂载每页独立会话，换页清空会话/token/流水线重新介绍当前页，规避 LLM 上下文猜错模块与用户所在页的矛盾。

面板按 pageCode 重挂载（`key={pageCode}`），**每页独立会话**：换页即清空对话框/sessionId/token/流水线，重新介绍当前页功能；在途 SSE 随卸载 cleanup 取消，不串页。**页面是唯一权威上下文，不做跨页历史维护**——规避"继续介绍指哪模块 / LLM 上下文猜错模块 vs 用户所在页"的矛盾。

**后端/模型可选对齐（不做不阻塞，前端已按页独立）**：
- Python `resolve_clarify`：`current_project` 为有效页面锚点且问题含指代词（"这个/当前/继续"）→ 直接按页面默认回答，不触发 clarify（"这个功能是干什么的"在知识图谱页 → 直接介绍知识图谱）。
- Java：换页可调 `close` 结算旧会话（F-M7 端点就绪后）；每页新 sessionId 天然独立记账。

### Risks / Trade-offs
> 状态：⚠️
> 检索摘要：风险与权衡：AI答疑页双聊天混淆、面板常驻占空间、后端桩替期与端点未建、页面→模块映射不完整靠缺省 rag-system 兜底。

- **AI答疑页双聊天混淆** → 该页不挂 RAG 助手（D2）。
- **面板常驻默认展开占用空间** → 右侧固定栏（~380px），收起留细条；不遮挡主内容。
- **后端桩替期**（M1–M4 后端未接真实链路）→ 前端按里程碑联调，事件缺省渲染空态。
- **E2E 依赖真实后端** → Playwright 用 `page.route` mock 完整 SSE 事件序列，不依赖后端。
- **后端端点未建（依赖后端 M3–M7）** → 联调时 Java 仅有 `/ask` + `/ask/sync`；`source`(F-M3)/`guide`(F-M6)/`eval/report`(F-M5)/`close`·`turns`(F-M7) 端点待后端建。F-M3 引用卡片可先用 rerank 事件数据渲染（"查看原文"待 source 端点），F-M6 引导待 guide 端点，F-M7 结算/补查待 close/turns 端点。
- **页面→模块映射不完整** → 缺省 rag-system 兜底；后续页面对应语料入库即自动可答。

### Migration Plan
> 状态：⚠️
> 检索摘要：迁移为纯前端增量：SSE client→面板改造（默认展开）→白盒阶段→引用/成本→引导/澄清→结算/补查；回滚恢复 FAB 抽屉。

- 纯前端增量：ragApi/SSE client → 面板改造（默认展开）→ 白盒阶段 → 引用/成本 → 引导/澄清 → 结算/补查。
- 回滚 = 移除面板改造与相关组件，AIChatPanel 恢复 FAB 抽屉（保留 `mode` 向后兼容）。

### Open Questions
> 状态：❓
> 检索摘要：开放问题：助手挂载范围是否含老师/管理员端占位、面板常驻宽度与主内容布局是否响应式收窄，本期演示以桌面为准。

- 助手挂载范围：**学生端 DashboardLayout 全部页面（除 AI答疑）默认展开**——确认是否也要在老师/管理员端展示占位？（后端仅 STUDENT）
- 面板常驻宽度与主内容布局是否要响应式收窄？本期演示以桌面为准。
