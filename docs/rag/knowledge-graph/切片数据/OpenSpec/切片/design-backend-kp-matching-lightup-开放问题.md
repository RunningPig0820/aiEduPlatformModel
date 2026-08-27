# Open Questions

> summary: Python mastery_signals 是否改名 topic_label、student_grade 来源、LLM 消歧调用方式、聚合阈值、掌握度自动迁移、topic_key 归一化力度等 8 项待决策。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-开放问题.md
> 类别：未来演进

> 检索摘要：Python mastery_signals 是否改名 topic_label、student_grade 来源、LLM 消歧调用方式、聚合阈值、掌握度自动迁移、topic_key 归一化力度等 8 项待决策。

0. **【高优先级·跨仓库协调】Python `mastery_signals` 信号源粒度**：现状 `kp_label` 是自由文本（题型/知识点混合，见 Context），要翻题型粒度需 Python 稳定输出**题型 label**。字段名 `kp_label` 是否重命名为 `topic_label`？（默认：建议重命名 `topic_label` 语义清晰，Java `MasterySignalItem` 对应改 `@JsonProperty`；Python 未就绪前 Java 侧兼容旧字段名 `kp_label` 作为过渡）。
1. **student_grade 来源**：组织系统查（学生→班级→年级）还是 `DecideRequest` 加 `student_grade` 契约字段？（默认：Java 解析时查组织系统，不改 Python 契约）。
2. **LLM 消歧调用方式**：复用 `llm-gateway`（Java 侧小调用）还是新增 Python 消歧端点？（默认：llm-gateway，避免动 Python）。
3. **聚合阈值初值**：CANDIDATE≥3 / STABLE≥10（默认采纳，可配置）。
4. **掌握度自动迁移**：本期只打标，是否后续做自动迁移？（默认：本期不做）。
5. **消费方**（变式题/错题分组）本期不做，题型库先沉淀数据。
6. **澄清卡数据契约**：候选概念 + 低置信状态从哪来——SSE meta 扩展，还是前端单独调 `POST /api/kp/resolve`？（默认：前端单独调 /api/kp/resolve，接口已返回 candidates，不改 decide meta + Python 契约）。
7. **topic_key 归一化力度**：字面归一化（全角半角/空白/去末尾语气词）初版是否够用，是否需同义词聚类（"鸡兔同笼"≈"鸡兔问题"）？（默认：本期只做字面归一化，同义词聚类留大数据阶段）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§Open Questions）
