# Python 为什么保持无状态？角色门、会话聚合为什么都放 Java？

> summary: Python 为什么保持无状态？角色门、会话聚合为什么都放 Java？
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-36-架构设计-Python为什么保持无状态角色门会话聚.md
> 类别：架构设计

---

## 回答

**核心结论**：Java 是天然聚合点（token/trace/session 每轮过手），角色从可信 session 取、body 传 role 忽略；Python 不自己认证、不碰会话、不落库，保住无状态边界可水平扩展。

**分层展开**：
- **为什么 Java 是聚合点**：token/trace/session 每轮过手（done 落库、累计、close 结算、turns 补查），天然适合做角色门 + 会话聚合（依据：完善文档 03 / 分析-08）。
- **角色从可信源取**：`requireStudent`→`TutoringAuth.isStudent` 从可信 HttpSession 取 role，仅 STUDENT 放行、非学生固定 403；**body 传 role 一律忽略**（`RagAskCommand` 无 role 字段，测试 RAG-GATE-004 验证"TEACHER session + body 带 role=STUDENT → 仍 403"）（依据：分析-08 / 完善文档 09）。
- **Python 无状态**：Python 只消费 history/trace_id，不产 permission（从 intent 开始）、不碰会话、不落库——保无状态边界、可水平扩展（依据：完善文档 03 / 分析-08）。
- **落地**：会话累计/close/turns/真实对话质量全归 Java Redis（`rag:assistant:*`，TTL 24h）；Python 只做检索问答编排（依据：分析-08）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 36 问）｜ `4.完善文档/03-为什么这么设计.md`、`09-权限与边界.md` ｜ `3.代码/分析-08-Java后端网关与SSE中继.md`
