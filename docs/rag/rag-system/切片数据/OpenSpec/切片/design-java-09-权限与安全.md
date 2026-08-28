# 权限与安全

> summary: 权限与安全（design-java-rag-project-intro-assistant）：角色门在Java可信session仅STUDENT放行、非学生固定403、禁信前端body传role、0 token不落trace，保持Python无状态边界
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-09-权限与安全.md
> 类别：业务流程

---

### D1. 角色门在 Java(可信 session),不在 Python,禁信 body

> 检索摘要：角色门为什么在Java可信session不在Python：仅STUDENT放行否则固定403，禁信前端body传role，保Python无状态边界

学生登录后 session 含 `userId`+角色;Java 网关从 `HttpSession.getAttribute("role")`(或网关 Header)取角色,`STUDENT` 才放行,否则固定 403 响应体(非 RAG 流程、不调 LLM、不落任何 trace)。前端任何 body 传 role 一律忽略。
- **为什么**:与 tutoring 认证桥接(方案 A)一致——前端走 Java 网关,Python 不自己认证、不碰会话;严禁信任前端传参(spec 硬性要求)。
- **备选**:Python 自校验 → 破坏"Python 无状态"边界,弃。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§D1. 角色门在 Java）
