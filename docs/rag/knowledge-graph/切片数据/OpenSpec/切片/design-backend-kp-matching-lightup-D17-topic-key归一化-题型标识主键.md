# topic_key 归一化（题型标识主键）

> summary: 题型标识用归一化 topic_key 作主键、topic_label 只展示，NFKC 全角半角/空白折叠/去末尾标点，SHALL NOT 剥离「问题」等题型固有后缀。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D17-topic-key归一化-题型标识主键.md
> 类别：数据存储

> 检索摘要：题型标识用归一化 topic_key 作主键、topic_label 只展示，NFKC 全角半角/空白折叠/去末尾标点，SHALL NOT 剥离「问题」等题型固有后缀。

**决策**：题型标识用归一化后的题型名 `topic_key` 作主键，`topic_label` 只作展示。归一化函数落 domain（`TopicKeyNormalizer`），规则：Unicode NFKC 全角→半角、trim + 空白折叠、去末尾标点（"鸡 兔 同 笼" / 全角写法 / 带标点 → 同一 key）。**SHALL NOT 剥离「问题/题型」等后缀**——「相遇问题/追及问题/工程问题」里的「问题」是题型名固有部分，剥离会丢语义（同义词聚类留大数据阶段）。

**理由**：题型空间无限且命名不规整（LLM 随手输出），自由文本直接作主键会导致同题型裂成多行、掌握度分散。归一化收敛到稳定 key，又与 `t_kp_derived_obs.topic_label` / `t_kp_question_type.topic_label` 对齐（题型库晋升后按 `topic_key` 关联）。冷启动首次遇到题型即可落掌握度，无需等题型库聚合——这是选 `topic_key` 而非 `question_type_id` 外键的核心原因（外键会冷启动断裂）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D17 topic_key 归一化（题型标识主键））
