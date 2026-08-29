# 白盒 SSE 链路的事件时序是什么样的？每个事件分别做什么？

> summary: 白盒 SSE 链路的事件时序是什么样的？每个事件分别做什么？
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-09-操作流程-白盒SSE链路的事件时序是什么样的每个事.md
> 类别：操作流程

---

## 回答

**核心结论**：冻结时序 `permission→intent→(clarify|switch)→rewrite→rerank→(boundary|token*)→done`，done 是所有分支唯一终止点；clarify/switch/boundary 分支无 generate、0 token 短路。

**分层展开**：
- **时序**：`permission`（Java 前置，含 traceId）→ `intent`（模块锚点+类别+switch/ambiguous 判断）→ `clarify` 或 `switch`（二选一分支）→ `rewrite`（追问改写）→ `rerank`（精排 Top-K 块）→ `boundary` 或 `token*`（二选一）→ `done`（唯一终止点）（依据：完善文档 02 / 分析-04）。
- **每个事件职责**：
  - `permission`：角色放行结果 + traceId（断线补查凭它）（依据：分析-08）。
  - `intent`：anchor/category/switchDetected/ambiguous/candidates 等意图信息（依据：分析-08）。
  - `clarify`：模糊问题候选 chips（candidates + default）；（依据：分析-08）。
  - `switch`：切模块提示 fromAnchor→toAnchor（依据：分析-08）。
  - `rewrite`：口语问题→检索式改写 originalQuestion→rewrittenQuery（依据：分析-08）。
  - `rerank`：精排 Top-K 块（先灰显折叠）（依据：分析-08）。
  - `token`：流式正文增量（前端逐字渲染）（依据：分析-09）。
  - `boundary`：范围门低置信拒答固定话术，reason="low_confidence"（依据：分析-08）。
  - `done`：最终答案 + quotedKeys + tokensUsage + traceId + suggestions（依据：分析-08）。
- **分支纪律**：clarify/switch/boundary 分支不发 rewrite/recall/generate、0 token 短路；done 到达即停所有转圈并定稿（依据：完善文档 02 / 分析-09）。
- **落地细节**：permission 由 Java 网关前置产，Python 生产端点从 intent 开始；done.answer 是全量答案，token 是增量（前端以 done 为准）（依据：分析-08）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 9 问）｜ `4.完善文档/02-核心功能.md` ｜ `3.代码/分析-04-检索编排.md`、`分析-08-Java后端网关与SSE中继.md`、`分析-09-前端白盒UI与交互.md`
