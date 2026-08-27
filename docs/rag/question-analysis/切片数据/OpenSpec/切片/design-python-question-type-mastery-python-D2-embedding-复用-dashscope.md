# D2：embedding 复用 dashscope OpenAI 兼容端点

> summary: embedding 复用 dashscope text-embedding-v3 显式 768 维（默认 1024 坑），索引维度建好不可改，余弦距离。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-question-type-mastery-python-D2-embedding-复用-dashscope.md
> 类别：架构设计

---

### D2：embedding 复用 dashscope OpenAI 兼容端点（不塞进 LLMFactory）

> 检索摘要：embedding 复用 dashscope text-embedding-v3 显式 768 维（默认 1024 坑），索引维度建好不可改，余弦距离。

`LLMFactory` 全是 `BaseChatModel`（对话），embedding 是向量编码，语义不同——**独立封装在 `vector_store.py`**，不污染既有 gateway（符合「gateway 配置不动」承诺）。

- 端点：`POST https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings`（与 `factory.py` bailian 同一 base）。
- 模型：`text-embedding-v3`，**显式 `dimensions=768`**（默认 1024，合法维度 1024/768/512/…；不显式指定则输出 1024，与索引维度对不上）。
- **选型背景**：`text-embedding-v3` 百炼**默认可用、无需开通**，直接选用不阻塞；`qwen3.7-text-embedding`（效果更好、免费额度翻倍）需开通，维度同为 768——**两者维度兼容，索引建好 768 后未来切 qwen3.7 只需换模型名，索引不重建**。
- **维度绑定约束（关键）**：索引维度必须 = embedding 输出维度，不能自由选大。put/query 两端都是同一个模型输出，维度不一致无法算相似度；**索引维度建好后不可改**。故 spike 顺序必须是「先验证 `dimensions=768` 实际输出 768 维 → 再建索引」，不可颠倒。
- **距离度量 = 余弦距离（已确认）**：文本语义检索标准，对向量长度不敏感（「鸡兔同笼」vs「鸡兔同笼的解法」语义相近余弦高）；与后端契约「768 维 cosine、distance 越小越相似」一致。排除欧氏距离（对 embedding 模长敏感，长文本被干扰）。
- 密钥：复用 `settings.DASHSCOPE_API_KEY`。
- 实现选择：`openai` SDK（requirements 已有）的 `client.embeddings.create`，或 `dashscope` SDK（已有）的 `text_embedding` 类——spike 定，优先 `dashscope` SDK（已装，官方 text-embedding-v3 示例多）。

> 证据：详见 `2.OpenSpec design 决策/design-python-question-type-mastery-python.md`（§D2）｜ 完善文档 06-题型动态聚集与向量.md
