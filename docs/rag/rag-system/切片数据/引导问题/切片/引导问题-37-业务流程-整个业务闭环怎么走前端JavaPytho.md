# 整个业务闭环怎么走？前端/Java/Python 三端各自承担什么？

> summary: 整个业务闭环怎么走？前端/Java/Python 三端各自承担什么？
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-37-业务流程-整个业务闭环怎么走前端JavaPytho.md
> 类别：业务流程

---

## 回答

**核心结论**：前端白盒面板（发起/点亮阶段/渲染引用/断线补查/close）；Java 角色门 + SSE 中继（snake→camel 重建）+ Redis 会话聚合；Python 检索问答编排（intent→召回→RRF→生成）无状态。

**分层展开**：
- **前端**：白盒面板发起 `POST /ask`（带 sessionId+history+currentProject）、按事件点亮 5 阶段行（权限→意图→改写→召回·重排→生成）、渲染引用块先灰后亮 + 查看原文、断线补查 turns、close 结算（依据：分析-09）。
- **Java**：角色门 `requireStudent`→`TutoringAuth.isStudent`（非 STUDENT 固定 403、0 token 不产 trace）；SSE 中继——桥保序透传（滤 permission 事件）+ `rebuildEvent` snake→camel 逐事件重建；Redis 会话聚合——累计 token/轮数、close 结算、turns 断线补查、真实对话质量打分（依据：分析-08）。
- **Python**：检索问答编排——intent→（clarify|switch）→rewrite→recall（双池三路）→orchestrate（四路 RRF×权威×锚定）→stream_generate→LCS 引用校验→done；显式无状态，只消费 history/trace_id（依据：分析-01 / 分析-04）。
- **闭环串起来**：前端发起 → Java 角色门产 permission（含 traceId）→ Python 白盒事件流 → Java 逐事件重建 camelCase 透传 → 前端渲染 + 引用回源 + 成本展示；断线走 turns 补查，结束走 close 结算（依据：分析-01 / 分析-08）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 37 问）｜ `4.完善文档/02-核心功能.md`、`04-数据流转.md` ｜ `3.代码/分析-01-整体架构与调用链.md`、`分析-08-Java后端网关与SSE中继.md`、`分析-09-前端白盒UI与交互.md`
