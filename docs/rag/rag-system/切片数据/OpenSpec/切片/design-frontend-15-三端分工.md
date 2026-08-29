# 三端分工
> summary: 三端分工
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-frontend-15-三端分工.md
> 类别：架构设计

---

> 检索摘要（业务向）：前端与 Java 网关/Python 引擎的边界怎么分工？Java 网关角色门+SSE 中继+source 代理，Python 无状态白盒链路；ask/source/close/turns/guide 端点谁提供、sessionId/traceId 契约在哪端累计？

### Context（三端契约）
> 检索摘要：后端契约已冻结：Java 网关角色门（仅 STUDENT）+ SSE 白盒事件中继；Python 白盒链路（intent/rewrite/recall/rerank/generate + clarify/is_quoted/分层超时/suggestions/tokens_usage）。

- 后端契约已冻结（`rag-project-intro-assistant`）：Java 网关角色门（仅 STUDENT）+ SSE 白盒事件中继；Python 白盒链路（intent/rewrite/recall/rerank/generate + clarify/is_quoted/分层超时/suggestions/tokens_usage）。

### D3: 模块 id 闭集（三端定稿）
> 检索摘要：模块 id 闭集三端定稿：rag-system 弃 rag-project、question-analysis 弃 question-type，前端/Java/Python 共用同一套模块 id。

每次 `ask` 携带 `currentProject`（camelCase）。模块 id 闭集三端定稿（**rag-system，弃 rag-project；question-analysis，弃 question-type**）——前端/Java/Python 三端共用同一套模块 id 契约。

| 模块 id | 业务模块 | 语料 |
|---|---|---|
| ai-tutoring | AI答疑 | 已有 234 块 |
| knowledge-graph | 知识图谱 | 未切片 |
| question-analysis | 题型分析 | 未切片 |
| rag-system | RAG 项目 | 未切片（9 节待跑） |

### D5: "查看原文" source 代理（Java 网关代理透传 Python）
> 检索摘要："查看原文" URL 定稿 GET /api/rag/assistant/source?path=，Java 网关代理透传 Python，STUDENT 角色门；前端拼 query 传参不走 path。

**"查看原文" URL 定稿**：`GET /api/rag/assistant/source?path=<urlencoded>`（Java 网关代理透传 Python，STUDENT 角色门）。前端**拼 query 传参，不走 path**（file_path 含 `http://` 前缀，走 path 会被容器拒）。

### D9: SSE 契约与累计端（Java 以 sessionId 为键累计）
> 检索摘要：前端 ragSse.js 读 POST /api/rag/assistant/ask（stream:true）SSE 流；permission.traceId 前端流开始即存；sessionId 前端生成 UUID，Java 以 sessionId 为键累计。

`src/utils/ragSse.js`：读取 `POST /api/rag/assistant/ask`（`stream:true`）SSE 流，按 event 类型分发（permission/intent/clarify/switch/rewrite/rerank/boundary/token/done），解析 camelCase 契约字段。

- **traceId 获取时机（定稿）**：`permission` 事件携带 `traceId`（`{role, allowed, traceId}`），前端**流开始即存**本轮 traceId——任意阶段断连都能补查；`done` 回显做一致性校验。
- **sessionId（定稿）**：前端**面板挂载时用 `llmApi.generateSessionId()` 生成 UUID**，整场会话复用；Java 以 sessionId 为键累计，ask 未知 session 按新会话。
- **ask 请求字段 camelCase**：`currentProject` / `question` / `sessionId` / `history` / `traceId` / `stream` / `topK`。
- **断线补查**：SSE 中断 → 用已存 traceId 调 `GET /api/rag/assistant/turns/{traceId}` 补查该轮；trace 过期（10002）→ 提示重发。

### D11: 后端/模型可选对齐（三端可选协作）
> 检索摘要：前端已按页独立会话，后端可选对齐：Python resolve_clarify 按页面锚点+指代词直接回答不触发 clarify；Java 换页可调 close 结算旧会话。

**后端/模型可选对齐（不做不阻塞，前端已按页独立）**：
- Python `resolve_clarify`：`current_project` 为有效页面锚点且问题含指代词（"这个/当前/继续"）→ 直接按页面默认回答，不触发 clarify（"这个功能是干什么的"在知识图谱页 → 直接介绍知识图谱）。
- Java：换页可调 `close` 结算旧会话（F-M7 端点就绪后）；每页新 sessionId 天然独立记账。

### 风险与权衡（三端依赖相关条目）
> 检索摘要：三端依赖风险：后端桩替期（M1–M4 未接真实链路）前端按里程碑联调事件缺省空态；后端端点未建（source/guide/eval/report/close/turns 依赖后端 M3–M7）。

- **后端桩替期**（M1–M4 后端未接真实链路）→ 前端按里程碑联调，事件缺省渲染空态。
- **后端端点未建（依赖后端 M3–M7）** → 联调时 Java 仅有 `/ask` + `/ask/sync`；`source`(F-M3)/`guide`(F-M6)/`eval/report`(F-M5)/`close`·`turns`(F-M7) 端点待后端建。F-M3 引用卡片可先用 rerank 事件数据渲染（"查看原文"待 source 端点），F-M6 引导待 guide 端点，F-M7 结算/补查待 close/turns 端点。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-frontend-rag-assistant-frontend.md`（§Context §D3 §D5 §D9 §D11 §Risks/Trade-offs）
