# 坑档案-J-KG1-匹配率17%LLM标准化
> summary: 匹配率 17%→97%：LLM 标准化预处理解决小学知识点与 EduKG 抽象概念结构错位
> 来源: 坑档案 ｜ 锚点: J-KG1 ｜ 节: 5.难点/坑档案.md
> COS路径: rag-slices/knowledge-graph/坑档案/坑档案-J-KG1-匹配率17%LLM标准化.md
> 类别：开发难点
> target: 开发对账

---

**1. 问题现象**：教材知识点到图谱知识点的匹配率只有 17%——1350 个教材知识点仅 229 个匹配成功（202 精确 + 27 LLM），1121 个未匹配（83%）。图谱页面上大量知识点「点不亮」，知识点总览大片空白。

**2. 触发流程**：`match_textbook_kp.py` 把教材知识点逐条与 EduKG Concept 匹配 → 先精确匹配（`exact_match`）→ 失败进 LLM 双模型投票 → 输出 `matches_kg_relations.json`。执行后统计：小学 940 个（69.6%）、初中 252、高中 158；而 EduKG 只有 1295 个抽象概念（函数/方程/几何），几乎没有小学具体知识点（"1-5的认识""连加连减"）。

**3. 根因分析**：**语义颗粒度错位**——教材知识点贴近教学场景（"1-5的认识""秒的认识"），EduKG 概念是抽象数学概念（"自然数""时间单位"）。修前直接用原始教材名去向量检索/LLM 投票 → 查询词与候选概念不在同一语义空间 → 精确匹配命中率低、LLM 投票也因为输入名太"教学化"而大量否决。`problems_and_solutions.md` §十二记录："69.6% 的教材知识点（小学）无法匹配 EduKG 抽象概念"。

**4. 排查过程**：跑完 `--stats` 看方法分布——精确 202/LLM 27/未匹配 1121；再按学段拆分布发现小学占 69.6% 且几乎全未匹配，定位是"教材名 ≠ 概念名"的结构错位，不是投票逻辑本身坏了。

**5. 解决方案 & 改动点**：引入 **LLM 标准化预处理**（`kp_normalizer.py`）两阶段匹配：先用 LLM 把教材名推断为抽象概念列表 + best_match（"1-5的认识"→"自然数"），再用标准名去向量检索 + 双模型投票。改动点：`edukg/core/textbook/kp_normalizer.py:69-279`（KPNormalizer.normalize 返回 concepts/best_match）、`edukg/core/textbook/kp_matcher.py:596-602`（`get_best_match` 优先用标准化名）、`edukg/scripts/kg_data/textbook/normalize_textbook_kp.py`。修复提交：`03f3f75 [知识图谱]-[教学知识点和知识点推断]`（新增 kp_normalizer + problems 文档 §十二）。最终数据 `edukg/data/edukg/math/5_教材目录(Textbook)/output/matches_kg_relations.json`：1905 总、1847 匹配（1639 精确 + 208 LLM）≈ 97%。

**6. 面试口述要点**：匹配率瓶颈不在"投票模型不强"，而在**输入与候选的语义空间不一致**——先用 LLM 做名称标准化（把教学名映射到概念名）是性价比最高的提点手段；匹配率 17%→97% 的关键是"把教材名翻译成图谱语言"再匹配，而不是盲目加模型。注意标准化本身有成本，所以标准化结果也走缓存（`normalizer_cache/`）。
