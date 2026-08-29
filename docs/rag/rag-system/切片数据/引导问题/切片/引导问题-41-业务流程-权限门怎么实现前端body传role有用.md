# 权限门怎么实现？前端 body 传 role 有用吗？

> summary: 权限门怎么实现？前端 body 传 role 有用吗？
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-41-业务流程-权限门怎么实现前端body传role有用.md
> 类别：业务流程

---

## 回答

**核心结论**：Java 网关 `RagAssistantController.requireStudent` → `TutoringAuth.isStudent` 从可信 HttpSession 取 role，仅 STUDENT 放行、非学生固定 403、0 token 不产 trace；**body 传 role 一律忽略**（`RagAskCommand` 无 role 字段）。

**分层展开**：
- **实现**：`requireStudent(session)`（Controller:117-123）→ `TutoringAuth.isStudent`（`"STUDENT".equals(session.getAttribute("role"))`）；角色缺失/无 session → 403；全局异常处理转 HTTP 403 + body `{code:"403", message:"仅学生可访问此助手"}`（依据：分析-08）。
- **body 传 role 有用吗**：没用——`RagAskCommand` **无 role 字段**，body 传 role 一律忽略；测试 RAG-GATE-004 明确验证"TEACHER session + body 带 role=STUDENT → 仍 403"（依据：分析-08 / 完善文档 09）。
- **代价**：非学生固定 403、0 token、不产 trace、不进 RAG 流程；permission 事件（含 traceId）由 Java 前置发，Python 生产端点从 intent 开始（依据：分析-08）。
- **边界**：Controller 的 `requireStudent` 只查 role、不查 userId（缺 userId 但 role=STUDENT 的会话理论可通过）；Python 侧所有端点只有 `verify_internal_token` 服务鉴权（依据：分析-08）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 41 问）｜ `4.完善文档/09-权限与边界.md` ｜ `3.代码/分析-08-Java后端网关与SSE中继.md`
