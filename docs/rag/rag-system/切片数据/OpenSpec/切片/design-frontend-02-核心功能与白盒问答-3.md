# 核心功能与白盒问答
> summary: 核心功能与白盒问答-3（SSE client/断线补查/防卡死/迁移/风险/开放问题）
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-frontend-02-核心功能与白盒问答-3.md
> 类别：操作流程

---

> 检索摘要（业务向）：前端 SSE client 怎么读取 ask 流并按事件分发驱动白盒链路？traceId/sessionId 契约怎么定、断线怎么补查？轮次怎么防卡死（done 终止 + 45s 超时）？纯前端增量迁移/回滚与开放问题是什么？

### D9: SSE client 与断线补查
> 检索摘要：ragSse.js 读取 SSE 流按事件类型分发；permission 事件携带 traceId 流开始即存；断线用 traceId 调 turns 接口补查，trace 过期提示重发。

`src/utils/ragSse.js`：读取 `POST /api/rag/assistant/ask`（`stream:true`）SSE 流，按 event 类型分发（permission/intent/clarify/switch/rewrite/rerank/boundary/token/done），解析 camelCase 契约字段。

- **traceId 获取时机（定稿）**：`permission` 事件携带 `traceId`（`{role, allowed, traceId}`），前端**流开始即存**本轮 traceId——任意阶段断连都能补查；`done` 回显做一致性校验。
- **sessionId（定稿）**：前端**面板挂载时用 `llmApi.generateSessionId()` 生成 UUID**，整场会话复用；Java 以 sessionId 为键累计，ask 未知 session 按新会话。
- **ask 请求字段 camelCase**：`currentProject` / `question` / `sessionId` / `history` / `traceId` / `stream` / `topK`。
- **断线补查**：SSE 中断 → 用已存 traceId 调 `GET /api/rag/assistant/turns/{traceId}` 补查该轮；trace 过期（10002）→ 提示重发。

### D10: 轮次防卡死（分支终止 + 超时自关闭）
> 检索摘要：done 是所有分支终止点，到达即停全部转圈并定稿；单轮 45s 超时前端主动取消本轮提示重试，防止无限转圈。

SSE 不是纯线性链路——`clarify`/`boundary`/`switch` 三个分支各有对应渲染，且 **`done` 是所有分支的终止点**：不管本轮走正常链路还是澄清/边界/切换，done（或 error）到达必须停掉所有"处理中"转圈、阶段区定稿。clarify 轮 done 带空 answer → 气泡回显 `clarify.message`，不空白。

**超时兜底（定稿）**：单轮 45s（后端桥 60s 超时的前端兜底）未收到 done/error → 前端主动取消本轮，提示"响应超时，已结束本轮，请重试"，恢复可输入。防止任何分支/后端异常导致无限转圈。

### Migration Plan
> 检索摘要：迁移为纯前端增量：SSE client→面板改造（默认展开）→白盒阶段→引用/成本→引导/澄清→结算/补查；回滚恢复 FAB 抽屉。

- 纯前端增量：ragApi/SSE client → 面板改造（默认展开）→ 白盒阶段 → 引用/成本 → 引导/澄清 → 结算/补查。
- 回滚 = 移除面板改造与相关组件，AIChatPanel 恢复 FAB 抽屉（保留 `mode` 向后兼容）。

### 风险与权衡（核心功能相关条目）
> 检索摘要：前端核心功能相关风险：AI答疑页双聊天混淆、面板常驻占空间、E2E 依赖真实后端（Playwright mock 兜底）。

- **AI答疑页双聊天混淆** → 该页不挂 RAG 助手（D2）。
- **面板常驻默认展开占用空间** → 右侧固定栏（~380px），收起留细条；不遮挡主内容。
- **E2E 依赖真实后端** → Playwright 用 `page.route` mock 完整 SSE 事件序列，不依赖后端。

### Open Questions
> 检索摘要：开放问题：助手挂载范围是否含老师/管理员端占位、面板常驻宽度与主内容布局是否响应式收窄，本期演示以桌面为准。

- 助手挂载范围：**学生端 DashboardLayout 全部页面（除 AI答疑）默认展开**——确认是否也要在老师/管理员端展示占位？（后端仅 STUDENT）
- 面板常驻宽度与主内容布局是否要响应式收窄？本期演示以桌面为准。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-frontend-rag-assistant-frontend.md`（§D9 SSE client 与断线补查 §D10 轮次防卡死 §Migration Plan §Risks/Trade-offs §Open Questions）
