# 冷启动 LLM 消歧：LLM 生成候选名 + 镜像校验

> summary: 冷启动候选生成改为 LLM 自由生成 N 个候选知识点名再回镜像 exact/LIKE 校验，题型名与知识点名两套词汇靠 LLM 跨词汇语义桥接。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D21-冷启动llm消歧-llm生成候选名-镜像校验.md
> 类别：操作流程

> 检索摘要：冷启动候选生成改为 LLM 自由生成 N 个候选知识点名再回镜像 exact/LIKE 校验，题型名与知识点名两套词汇靠 LLM 跨词汇语义桥接。

**决策**：现 `KpLlmDisambiguator` 候选只来自 `findByLabelLikeList(label)`（镜像知识点名 LIKE），题型名（"鸡兔同笼"）在知识点名里 LIKE 不到 → 候选空 → LLM 不被调用 → 冷启动断、题型库长不出来。改为**两段式**：

```
③ LLM 消歧（冷启动，题型库无先验时）
  1. LLM 生成候选名：给定题型 label + 年级上下文，LLM 自由生成 N 个候选知识点名（"二元一次方程组"/"假设法"...）
  2. 镜像校验：Java 用 findByLabel(exact) / findByLabelLike(LIKE) 回镜像校验，命中才保留
     → 单候选命中 → RESOLVED（仍标 WEAK，见 Decision 9）
     → 多候选命中 → PENDING + 候选列表，弹澄清卡给学生选
     → 零命中 → PENDING（无候选，纯挂起）
```

**理由**：题型名和知识点名是两套词汇，靠「知识点名 LIKE 题型名」召回候选是死路。LLM 有跨词汇语义能力，能"由鸡兔同笼想到二元一次方程组"；但 LLM 会幻觉，所以候选名必须回镜像校验，最终 kp 必在镜像。这不算违背 Decision 2 的「SHALL NOT 凭空生成 kp」——LLM 只生成 **name 候选**，kp 本身经镜像校验存在。

**冷启动弱化沿 Decision 9**：首条 LLM 消歧标 `WEAK`，第二独立信号（第二名同学共现 / 学生投票达标 / 做题结果佐证）才转 RESOLVED。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D21 冷启动 LLM 消歧：LLM 生成候选名 + 镜像校验）
