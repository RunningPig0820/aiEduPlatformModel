# 向量 key 规则是什么？为什么必须带 module 段？

> summary: 向量 key 规则是什么？为什么必须带 module 段？
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-51-数据存储-向量key规则是什么为什么必须带modu.md
> 类别：数据存储

---

## 回答

**核心结论**：key=`{rag-full|rag-slice}/{module}/{file}/{anchor}#{idx}`（切片池每块再加 `-c`/`-q` 后缀）；带 module 段是 K10 修复——多模块共用同一物理索引，否则跨模块同名文件后写覆盖先写、keymap 只剩后写块。

**分层展开**：
- **key 规则**：`{池前缀}/{module}/{file}/{anchor}#{idx}`——池前缀 = `rag-{tags.pool}`（rag-full / rag-slice）决定桶 + 索引路由；切片池每块写 2 个 key，加 `-c`（内容路 embed(summary+text)）/ `-q`（问题路 embed(summary)）后缀（依据：分析-03 / 分析-01）。
- **为什么必须带 module**：K10 修复——多模块共用同一物理索引（rag-full/rag-slice），不带 module 段时跨模块同名文件（每模块都有"完善文档 01-08"）生成相同 key，COS 向量桶按 key upsert **后写覆盖先写**，keymap 只剩后写块（依据：坑档案 K10）。
- **build/query 同规则**：`build_index.make_key`（`build_index.py:59-65`）与 `query._key_of`（`query.py:584-592`）同规则，保证向量命中后能反查本地 jsonl（依据：分析-03）。
- **关联注意**：`--clear` 清的是整个池不分模块——多模块共池下清池会连其他模块向量一起删，需重灌全部模块（依据：分析-03）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 51 问）｜ `4.完善文档/08-数据规模与指标.md` ｜ `3.代码/分析-03-索引与向量库.md` ｜ `5.难点/坑档案-开发与验证.md`（K10）
