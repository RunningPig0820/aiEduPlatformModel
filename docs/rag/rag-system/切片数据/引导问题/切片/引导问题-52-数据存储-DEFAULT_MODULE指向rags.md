# DEFAULT_MODULE 指向 rag-system 但现在没语料，意味着什么？

> summary: DEFAULT_MODULE 指向 rag-system 但现在没语料，意味着什么？
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-52-数据存储-DEFAULT_MODULE指向rags.md
> 类别：数据存储

---

## 回答

**核心结论**：`query.py` `DEFAULT_MODULE="rag-system"` 未传 module 时 Filter 筛向无数据模块 → 向量 0 命中 → `anchor=rag-system` 的问题当前必然边界拒答；这是"语料整理中"过渡态，语料入 `MODULE_DATA` 即自动可答。

**分层展开**：
- **现状**：`query.py:455` `DEFAULT_MODULE="rag-system"`，未传 module 时 `build_filter({"module":{"$eq":"rag-system"}})`；但 `MODULE_DATA` 无 rag-system jsonl（仅 ai-tutoring + question-analysis）→ 向量 0 命中 → orchestrate 无命中 → 范围门/拒答（依据：分析-03 / 分析-01）。
- **意味着什么**：这是"语料整理中"的**过渡态**，不是产品边界——当前 API 路径 `current_project` 默认 "ai-tutoring" 兜底才不触发；但若触发 `DEFAULT_MODULE`，就是潜在隐患（悬空默认值）（依据：分析-03）。
- **何时自动可答**：rag-system 语料切片入 `MODULE_DATA` + 引导问题同步 `GUIDE_POOL["rag-system"]` 5 组后，`anchor=rag-system` 自动可答——**数据驱动、无代码改动**（语料白名单本身就是权限层，入库即放行）（依据：完善文档 01 / 引导问题.md 第 56 问）。
- **相关不一致**：guide 缺省/未知 → `FALLBACK_MODULE=ai-tutoring`；ask 请求 `current_project` 缺省 → `rag-system`——两入口缺省不同，前端不传时易"引导题与检索池不匹配"（依据：分析-05）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 52 问）｜ `4.完善文档/01-产品定位.md` ｜ `3.代码/分析-03-索引与向量库.md`、`分析-05-引导问题链路.md`
