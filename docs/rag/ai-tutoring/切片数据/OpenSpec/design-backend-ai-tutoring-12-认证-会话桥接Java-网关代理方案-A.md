# design-backend-ai-tutoring

> summary: AI辅导通过Java网关代理实现认证与会话桥接
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 12. 认证/会话桥接：Java 网关代理（方案 A）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> 类别：架构设计

---

### 12. 认证/会话桥接：Java 网关代理（方案 A）

前端统一走 Java 网关；Java 校验 `HttpSession.getAttribute("userId")`（STUDENT 角色）后，调 Python 时携带**内部 token + userId + sessionId**（复用 llm-gateway 的 `internalToken` 模式）。Python 不自己做认证，只信网关注入的身份。请求体不传 student_id。
