# 三端分工
> summary: 三端分工
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-frontend-ui-15-三端分工.md
> 类别：架构设计

---

> 检索摘要（业务向）：前端 spec 消费的后端契约面有哪些端点？ask（SSE 白盒事件）/source（查看原文 query 传参）/close（会话结算）/guide（开始引导）/turns（断线补查 traceId，过期 10002）；STUDENT 角色门在 Java 网关，前端非学生不发起 ask——三端边界怎么划？

### Requirement: 后端契约面（前端依赖的 Java 网关端点与角色门）
> 检索摘要：前端 spec 各 Requirement 依赖的后端端点集：ask/source/close/guide/turns 均由 Java 网关提供，STUDENT 角色门拦截非学生，前端消费白盒 SSE 事件契约。

前端 RAG 助手 UI 规格整体依赖 Java 网关提供以下端点与契约（前端只消费、不直连 Python 引擎；Python 无状态白盒链路在网关后）：

- **ask 问答（SSE 白盒流）**：`POST /api/rag/assistant/ask`（`stream:true`），请求携带 `currentProject`（页面锚点，见主题 4 块）；SSE 事件序列 `permission → intent → (clarify|switch) → rewrite → rerank → (boundary) → token → done` 驱动白盒流水线阶段行（见主题 2 块）。
- **source 查看原文**：`GET /api/rag/assistant/source?path=<urlencoded>`，**query 传参**；引用面板 filePath 可点击查看原文（见引用面板 Requirement）。
- **close 会话结算**：`POST /sessions/{sessionId}/close`，返回会话累计 token 与轮数，"结束对话"按钮调用（见成本展示与会话结算 Requirement）。
- **guide 开始引导**：`GET /guide`，进入时拉取 RAG 定向开始引导 chips（见引导完整 Requirement）。
- **turns 断线补查**：`GET /api/rag/assistant/turns/{traceId}`，SSE 中断用 `permission` 携带的 traceId 补查该轮；trace 过期返回 **10002** → 提示重发；`done` 回显 traceId 与 permission.traceId 比对做一致性校验（见断线补查 Requirement）。
- **STUDENT 角色门**：面板读取当前用户角色并在头部展示；角色非 STUDENT 展示"当前非学生无法使用"占位、**不发起 ask**（Java 网关 403 兜底，见非学生占位 Requirement）。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-frontend-rag-assistant-frontend-rag-assistant-ui.md`（§Requirement 引用面板 §成本展示与会话结算 §引导完整 §断线补查 §非学生占位 §当前页面锚点携带）
