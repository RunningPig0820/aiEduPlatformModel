# embedding 模型本地 vs API 怎么选？成本怎么算？

> summary: embedding 模型本地 vs API 怎么选？成本怎么算？
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-72-数据存储-embedding模型本地vsAPI怎么.md
> 类别：数据存储

---

## 回答

**核心结论**：落地选 dashscope text-embedding-v3（API）768 维，方案把本地 bge 当免费备选/demo 兜底（成本叙事=本地 bge 免费 embedding vs API 按 token 计费）；选型要点：维度建好不可改、换模型=全量重建，且 embedding token 未抓 usage 是半修点（诚实标注）。

**分层展开**：
- **落地选型**：`vector_store.py:26-29` 显式 text-embedding-v3、768 维，base=dashscope OpenAI 兼容端点 `https://dashscope.aliyuncs.com/compatible-mode/v1`，复用 DASHSCOPE_API_KEY（依据：分析-03）。
- **本地 vs API**：方案把本地 bge（BAAI/bge-small-zh）当免费备选/demo 兜底；API 按 token 计费——成本叙事=本地 bge 免费 embedding vs API 按 token 计费（依据：语雀总揽 §7.2/§1）。
- **选型要点**：COS 索引维度建好不可改、换模型/换维度 = 全量重建，维度决策是"一次锁死"——生产走 API 时先定好维度与索引（依据：完善文档 05 追问段 / 分析-03）。
- **⚠️ 半修点**：embedding 调用 token 未抓 usage（`vector_store.embed()` 不读 resp.usage.total_tokens），embedding 侧成本单列落空；生成成本真算用 doubao 单价 ¥0.003/0.009 千 token（依据：分析-07 / 坑档案 A2 / 分析-06 calc_cost）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 72 问）｜ `1.语雀/语雀-方案总揽.md`（§7.2/§1）｜ `3.代码/分析-03-索引与向量库.md`（embedding）、`分析-07-API降级与容错.md` ｜ `5.难点/坑档案-开发与验证.md`（A2）
