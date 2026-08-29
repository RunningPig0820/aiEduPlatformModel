# rag-system 自身语料整理完成后会发生什么？要改代码吗？

> summary: rag-system 自身语料整理完成后会发生什么？要改代码吗？
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-56-未来演进-ragsystem自身语料整理完成后会发.md
> 类别：未来演进

---

## 回答

**核心结论**：语料切片入 `MODULE_DATA` + 引导问题同步 `GUIDE_POOL["rag-system"]` 5 组后，`anchor=rag-system` 自动可答——**数据驱动、无代码改动**（语料白名单本身就是权限层，入库即放行）。

**分层展开**：
- **数据侧发生什么**：本模块语料（问题列表/合成问答/问答切片）整理完成 → 切片成 `rag_slices-rag-system.jsonl` + `rag_slices_full-rag-system.jsonl` → 入 `MODULE_DATA` → `build_index` 入 `rag-full`/`rag-slice` 向量桶 → `DEFAULT_MODULE="rag-system"` 的悬空默认被填实（依据：分析-03 / 引导问题.md 第 56 问）。
- **引导侧同步**：问题列表同步 `GUIDE_POOL["rag-system"]` 5 组（intro/operation/data_relation/difficulty/rag），guide 入口题/结束建议不再兜底 ai-tutoring 池（依据：分析-05）。
- **要改代码吗**：**不需要**——`anchor=rag-system` 当前"必然边界拒答"的过渡态自动解除；语料入库即放行（语料白名单本身就是权限层），这是设计好的数据驱动路径（依据：完善文档 01 / 引导问题.md 第 56 问）。
- **一个代码前提**：若要多模块评测，`eval_dataset` 硬编码 `module=="ai-tutoring"` 需先改（与 rag-system 语料就绪无关，是评测侧独立事项）（依据：分析-06）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 56 问）｜ `4.完善文档/01-产品定位.md` ｜ `3.代码/分析-03-索引与向量库.md`、`分析-05-引导问题链路.md`、`分析-06-评测.md`
