# 多轮对话怎么保持上下文锚定？（current_project/history）

> summary: 多轮对话怎么保持上下文锚定？（current_project/history）
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-75-操作流程-多轮对话怎么保持上下文锚定current.md
> 类别：操作流程

---

## 回答

**核心结论**：模块锚定 current_project——前端页面 pageCode→模块 id 闭集 + intent LLM 判 anchor、失败回退关键词两层 + 指代词确定性兜底 `_deictic_anchor`（"这个功能"=当前模块，防硬路由跳 rag-system）；history 最近 3 轮喂 intent/rewrite；会话聚合归 Java Redis（trace 快照 TTL 24h）保证断线补查。

**分层展开**：
- **模块锚定两层**：前端页面 pageCode→模块 id 闭集（ai-tutoring/knowledge-graph/question-analysis/rag-system）+ intent LLM 结构化输出 anchor、失败回退关键词两层（模块 `_fallback_module` + 节 `_fallback_anchor`）；向量层再按 module Filter 选池（依据：分析-04 / 完善文档 03）。
- **指代词兜底（K8）**：`_deictic_anchor`——问题含"这个功能/它/本功能/当前功能/这个项目"且未点名其他模块 → 强制 anchor=current_project；否则"这个功能的底层是怎么实现的"会被 LLM/规则硬路由到 rag-system（无语料）必然拒答（依据：坑档案 K8 / 分析-04 query.py:275-290）。
- **历史管理**：history 最近 3 轮（HISTORY_LIMIT=3）喂 intent/rewrite，上下文不膨胀；会话状态/累计 token/trace 快照归 Java Redis（TTL 24h），断线补查凭 traceId（依据：分析-04 / 分析-08）。
- **⚠️ 缺口**：guide/ask 缺省不一致——guide 缺省/未知 → FALLBACK_MODULE=ai-tutoring，ask 缺省 → rag-system；前端不传时引导题与检索池可能错位（依据：坑档案 A7）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 75 问）｜ `3.代码/分析-04-检索编排.md`（intent/_deictic_anchor）、`分析-08-Java后端网关与SSE中继.md` ｜ `4.完善文档/03-为什么这么设计.md` ｜ `5.难点/坑档案-开发与验证.md`（K8/A7）
