# 解析管线：年级锚 + 镜像 + 题型库先验 + LLM 消歧 + 挂起

> summary: TutoringKpResolverImpl 重写为五步解析管线：镜像精确/LIKE→题型库年级匹配→LLM 消歧→学生澄清→挂起，年级是强先验非硬规则。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D2-解析管线-年级锚-镜像-题型库先验-llm消歧-挂起.md
> 类别：数据关联

> 检索摘要：TutoringKpResolverImpl 重写为五步解析管线：镜像精确/LIKE→题型库年级匹配→LLM 消歧→学生澄清→挂起，年级是强先验非硬规则。

**决策**：`TutoringKpResolverImpl` 重写为管线，命中顺序：

```
① kg 镜像精确 / LIKE（现有逻辑，0 成本）
② 题型库 grade-matched（STABLE/CANDIDATE 中按学生年级取占比最高 kp → 数据驱动先验）
③ LLM 消歧（topic + 镜像/题型库候选 label 列表 → LLM 选最匹配 + 置信度）
④ 低置信/歧义 → 学生澄清（可选，见 Decision 8 信任模型）→ 学生选则落 source=student_vote 观测
⑤ 学生跳过或仍歧义 → PENDING → 落 t_kp_derived_obs(status=PENDING) → 挂起，不点亮
```

**年级锚**：学生年级是"同一题型不同年级归不同 kp"的主信号（鸡兔同笼：四/五年级→假设法，七年级→二元一次方程组）。年级来自组织系统（学生→班级→年级），图谱 URI 内嵌年级（`renjiao-g1s`=一年级上）可距离排序。**年级是强先验非硬规则**：跨年级薄弱是 feature，LLM 上下文 + 置信度可覆盖。

**LLM 消歧接入**：复用现有 `llm-gateway`（或 Python 消歧端点），开放决策见 Open Questions。

**候选列表质量**：③ 冷启动消歧的候选生成见 Decision 21（LLM 生成候选名 + 镜像校验）；题型库已有先验时优先走②年级匹配，LLM 只兜底。最终 kp 必经镜像校验（SHALL NOT 凭空生成镜像不存在的 kp）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D2 解析管线：年级锚 + 镜像 + 题型库先验 + LLM 消歧 + 挂起）
