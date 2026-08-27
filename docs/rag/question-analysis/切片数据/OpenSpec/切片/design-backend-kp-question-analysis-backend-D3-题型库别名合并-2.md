# 题型库别名合并（续）

> summary: 题型库别名合并：kp 分布重叠≥70% 判变体折叠进 canonical + 别名表，查询统一走别名，canonical 只增不改。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D3-题型库别名合并-2.md
> 类别：数据关联

---

### D3：题型库别名合并——kp 分布重叠 → canonical + 别名表（续）

> 检索摘要：题型库别名合并：kp 分布重叠≥70% 判变体折叠进 canonical + 别名表，查询统一走别名，canonical 只增不改。

#### 查询统一走别名

查询统一改 `findByTopicLabel(label)` → `findByTopicLabelOrAlias(label)`，覆盖：解析管线② `resolveByCatalog`、`recordStudentVote`、analyze-question、聚合步骤①。实现 = 一条 LEFT JOIN（alias→question_type）或先查 canonical 再查 alias 兜底。

#### 判变体依据：kp 分布重叠

**为什么按 kp 分布重叠而非归一化/字符串相似**：变体题型的**语义锚是它指向的知识点**（同一批 obs 的 kp_uri），重叠是确定性信号、零 LLM、零误判成本（两个不同题型共享一个知识点不会触发 70% 重叠）。字符串/归一化兜不住「鸡兔同笼」vs「鸡兔同笼问题」，kp 重叠天然兜住。LLM 级同义词（「牛吃草」vs「牛顿问题」无 kp 重叠但语义相近）留大数据阶段。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D3，下半）｜ 语雀-决策记录.md D22 ｜ 完善文档 06-题型动态聚集与向量.md
