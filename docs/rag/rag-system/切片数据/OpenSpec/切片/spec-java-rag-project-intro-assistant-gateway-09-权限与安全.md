# 权限与安全（学生角色硬门）

> summary: 学生角色硬门：可信session取角色不信任body传参、非STUDENT固定403不消耗token不产生trace
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-java-rag-project-intro-assistant-gateway-09-权限与安全.md
> 类别：业务流程

---

### Requirement: 学生角色硬门
> 检索摘要：为什么角色门从可信session取角色而不信任前端body传参？非STUDENT是否固定403、不消耗token不产生trace？

系统 SHALL 在 RAG 助手请求入口从可信源（`HttpSession` 或网关解析 Header）获取当前用户角色，禁止信任前端 body 传参；仅当角色明确为 `STUDENT` 时放行进入 RAG 流程，否则返回固定 403 拒绝响应。

#### Scenario: 学生放行

- **WHEN** 已登录学生（session 角色=STUDENT）发送 `POST /api/rag/assistant/ask`
- **THEN** 系统进入 RAG 流程，透传 SSE 白盒事件

#### Scenario: 非学生拒绝

- **WHEN** 已登录用户角色为 TEACHER/ADMIN（或其它非 STUDENT 角色）发送请求
- **THEN** 系统返回固定 403 响应体（如"仅学生可访问此助手"），**不进入 RAG 流程、不调用 LLM、不消耗任何 token、不产生 trace**

#### Scenario: 角色缺失

- **WHEN** 请求无有效会话或角色缺失
- **THEN** 系统返回固定 403 响应体，同样不进入 RAG 流程

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-java-rag-project-intro-assistant-gateway.md`（§学生角色硬门）
