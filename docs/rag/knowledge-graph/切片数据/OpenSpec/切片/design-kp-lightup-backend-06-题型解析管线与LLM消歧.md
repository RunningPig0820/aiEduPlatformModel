# 题型解析管线与LLM消歧

> summary: 题型解析管线与LLM消歧
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kp-lightup-backend-06-题型解析管线与LLM消歧.md
> 类别：架构设计

---

> 检索摘要：TutoringKpResolverImpl 重写为五步解析管线（镜像精确/LIKE → 题型库年级匹配 → LLM 消歧 → 学生澄清 → 挂起），年级是强先验非硬规则；冷启动 LLM 生成候选名必须回镜像校验，首条消歧标 WEAK 不直接点亮。

**D2 解析管线：年级锚 + 镜像 + 题型库先验 + LLM 消歧 + 挂起**

TutoringKpResolverImpl 重写为管线，命中顺序：
1. kg 镜像精确 / LIKE（现有逻辑，0 成本）
2. 题型库 grade-matched（STABLE/CANDIDATE 中按学生年级取占比最高 kp → 数据驱动先验）
3. LLM 消歧（topic + 镜像/题型库候选 label 列表 → LLM 选最匹配 + 置信度）
4. 低置信/歧义 → 学生澄清（可选，见信任模型）→ 学生选则落 source=student_vote 观测
5. 学生跳过或仍歧义 → PENDING → 落 t_kp_derived_obs(status=PENDING) → 挂起，不点亮

年级锚：学生年级是「同一题型不同年级归不同 kp」的主信号（鸡兔同笼：四/五年级→假设法，七年级→二元一次方程组）。年级来自组织系统（学生→班级→年级），图谱 URI 内嵌年级（renjiao-g1s=一年级上）可距离排序。年级是强先验非硬规则：跨年级薄弱是 feature，LLM 上下文 + 置信度可覆盖。LLM 消歧接入：复用现有 llm-gateway（或 Python 消歧端点），开放决策见待决问题。候选列表质量：冷启动消歧的候选生成见 D21；题型库已有先验时优先走②年级匹配，LLM 只兜底。最终 kp 必经镜像校验（SHALL NOT 凭空生成镜像不存在的 kp）。

**D21 冷启动 LLM 消歧：LLM 生成候选名 + 镜像校验**

现 KpLlmDisambiguator 候选只来自 findByLabelLikeList(label)（镜像知识点名 LIKE），题型名（「鸡兔同笼」）在知识点名里 LIKE 不到 → 候选空 → LLM 不被调用 → 冷启动断、题型库长不出来。改为两段式：
1. LLM 生成候选名：给定题型 label + 年级上下文，LLM 自由生成 N 个候选知识点名（「二元一次方程组」/「假设法」……）
2. 镜像校验：Java 用 findByLabel(exact) / findByLabelLike(LIKE) 回镜像校验，命中才保留 → 单候选命中 → RESOLVED（仍标 WEAK）；多候选命中 → PENDING + 候选列表，弹澄清卡给学生选；零命中 → PENDING（无候选，纯挂起）

理由：题型名和知识点名是两套词汇，靠「知识点名 LIKE 题型名」召回候选是死路。LLM 有跨词汇语义能力，能「由鸡兔同笼想到二元一次方程组」；但 LLM 会幻觉，所以候选名必须回镜像校验，最终 kp 必在镜像。这不算违背 D2 的「SHALL NOT 凭空生成 kp」——LLM 只生成 name 候选，kp 本身经镜像校验存在。

**D9 冷启动弱化：首条 LLM 消歧不直接点亮**

题型库无先验支撑时（冷启动首条），LLM 消歧结果 SHALL 标记 status=WEAK（弱确定），不直接点亮、不直接进题型库先验；满足任一「第二独立信号」才转 RESOLVED：① 同生后续做题结果佐证（用该知识点解对了同类题）；② 第二名不同学生对该题型消歧到同一 kp（共现佐证）；③ 学生澄清投票达到阈值且方向一致。理由：冷启动种子 100% 依赖 LLM，是最不可靠的一环。让「确定性」来自「重复 + 客观结果」而非 LLM 一句话，防止高置信幻觉直接结晶。
