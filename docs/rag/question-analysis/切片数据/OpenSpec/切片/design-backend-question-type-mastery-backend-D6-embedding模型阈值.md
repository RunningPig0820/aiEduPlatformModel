# embedding 模型 + 阈值

> summary: embedding 用 dashscope text-embedding-v3（768 维），归并阈值 distance≤0.2 保守，宁可拆不误并。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-question-type-mastery-backend-D6-embedding模型阈值.md
> 类别：数据关联

---

### Decision 6：embedding 模型 + 阈值——dashscope 优先，spike 已实测（distance 契约，后端收口）

> 检索摘要：embedding 用 dashscope text-embedding-v3（768 维），归并阈值 distance≤0.2 保守，宁可拆不误并。

- **模型**：dashscope text-embedding-v3（768 维，中文 50+ 语种，OpenAI 兼容）——Python gateway 已接 dashscope，**成本已确认**（免费 50 万 token + 0.5 元/百万 token，10 块钱够用很久）。**已交付**：独立封装在 `vector_store.py`（未动 gateway factory），复用 `DASHSCOPE_API_KEY`。
- **备选**：ark doubao-embedding（火山，Python gateway 也接）；本地开源模型（text2vec/m3e，需 Python 部署）。
- **spike 实测（Python 端交付）**：cosine **distance（越小越相似，非相似度）**——self ≈ 0、同型 ~0.077（鸡兔同笼→鸡兔同笼问题）、异型 ≥0.33（相遇→行程 0.332、鸡兔同笼 vs 异型 0.481）。同型/异型在 **~0.08~0.33 有清晰间距**。
- **阈值 = 归并旋钮（distance ≤ X 归并，代码按 distance 判定）**：保守默认 **0.2**（只并同型，不并异型；宁可拆不误并）、激进 **0.25**（逼近 0.33 异型下限）。「相遇 vs 行程」（0.332）不被 0.2 归并——**默认拆分**。后端收口后入 `application.yml`。

> 证据：详见 `2.OpenSpec design 决策/design-backend-question-type-mastery-backend.md`（§Decision 6）｜ 语雀-决策记录.md D6/D7 ｜ 完善文档 06-题型动态聚集与向量.md ｜ 坑档案 J-QT4
