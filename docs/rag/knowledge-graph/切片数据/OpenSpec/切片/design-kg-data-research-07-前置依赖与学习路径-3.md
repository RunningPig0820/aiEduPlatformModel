# 前置依赖与学习路径：多证据融合与质量验证

> summary: 前置依赖与学习路径（多证据融合与质量验证）
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-data-research-07-前置依赖与学习路径-3.md
> 类别：数据关联

---

> 检索摘要：多证据怎么融合、PREREQUISITE 质量怎么保证？定义依赖强证据直接生成 PREREQUISITE(0.85)，LLM 两模型一致且≥0.8 生成(已有则+0.1封顶1.0)否则降 PREREQUISITE_CANDIDATE；年级倒置按跨度惩罚 ×0.95/0.9/0.5/0.3，惩罚后<0.6 降级候选；DFS 环检测移除最低置信边保 DAG；抽样准确率≥70%。

**多证据融合（状态：）**——EVIDENCE_WEIGHTS = {definition_dependency: 0.85, llm_inference: 0.8}
- 定义依赖：强证据，直接生成 PREREQUISITE（confidence 0.85，evidence_types=[definition_dependency]，source=definition_extraction）
- LLM 候选：两模型一致且置信度 ≥0.8 → PREREQUISITE；若该关系已有定义依赖则 confidence = min(1.0, 原值+0.1) 并追加 llm_inference 证据；<0.8 → 存入 PREREQUISITE_CANDIDATE
- 教材顺序：仅作为 TEACHES_BEFORE，不转化为 PREREQUISITE
- 融合规则总结：定义依赖→PREREQUISITE；LLM 候选两模型一致+≥0.8→PREREQUISITE，否则→CANDIDATE；教材顺序→TEACHES_BEFORE

**置信度处理（状态：）**：<0.8 的 LLM 候选→PREREQUISITE_CANDIDATE；定义依赖→直接生成 PREREQUISITE；LLM 多模型投票一致+≥0.8→PREREQUISITE；年级倒置按跨度惩罚置信度。

**年级倒置的宽松处理（智谱建议，状态：）**：原方案将"高年级指向低年级"直接判定为异常，但跨学段复习或螺旋式课程设计合理（如高二物理用到初三数学知识）。改进：GRADE_ORDER 小学 1-6/初中 7-9/高中 10-12，按前置年级-目标年级跨度惩罚：

| 年级跨度 | 示例 | 置信度惩罚 | 处理方式 |
|---|---|---|---|
| 0-2（相邻） | 高一→初三数学基础 | ×0.95 | 正常，保留 PREREQUISITE |
| 3（跨1学段） | 高二→初三 | ×0.9 | 合理但需确认 |
| 4-6（跨2学段） | 高中→小学 | ×0.5 | 存入 PREREQUISITE_CANDIDATE |
| >6（跨度太大） | 高三→小学一年级 | ×0.3 | 存入 PREREQUISITE_CANDIDATE |

惩罚后置信度 <0.6 降级为 PREREQUISITE_CANDIDATE；前置年级 ≤ 目标年级（span≤0）不惩罚。

**验证方式（Demo 务实策略，状态：）**：自动验证（循环依赖检测、年级倒置检测，数据导入前自动执行）+ 抽样测试（随机抽取检查合理性，准确率 ≥70% 即可满足 demo）+ 人工审核（教师审核，Demo 不做，无相关人员）。

**循环依赖检测（状态：）**：A→B 且 B→A 形成有向环，违背 DAG 要求；DFS 检测环，resolve_cycles 移除环中置信度最低的边，保证前置关系符合 DAG。

**孤立知识点检测（状态：）**：没有任何 PREREQUISITE 关系也没被依赖的知识点，可能是原子知识点或数据缺失；按入度/出度区分——isolated（定义/定理型，真正孤立）vs potential_missing（非定义/定理型，可能数据缺失），辅助定位数据问题。

**分层抽样评估（状态：）**：按关系来源分组抽样（默认 100 条）；评估标准——定义依赖（强合理=定义中直接包含前置概念/弱合理=间接引用/不合理=匹配错误）、LLM 推理（明确必须掌握/较强辅助作用/完全无关）、教材顺序（仅时间依赖）。

**置信度校准（状态：）**：对比模型置信度与专家打分，校准因子 calibration_factor = avg_human/avg_model，识别模型过自信（avg_model>avg_human）或保守，便于后续阈值调整。

**抽样测试量化（状态：）**：从数学随机抽 100-200 条 PREREQUISITE 覆盖不同年级/类型，准确率=合理关系数/抽样总数，目标 ≥70%；低于阈值调整策略：① 调整 Prompt 设计（增加 Few-Shot 示例）② 降低 temperature（如 0.2）③ 提高置信度阈值（如 0.85）。

**图谱质量指标（状态：）**

| 指标 | 计算方法 | 目标值(demo) |
|---|---|---|
| 前置关系覆盖率 | 有 PREREQUISITE 关系的知识点数 / 总知识点数 | ≥30% |
| DAG 合规率 | 无环的知识点比例（检测环的数量） | 100% |
| 平均前置链长度 | 所有知识点最长前置路径长度的平均值 | 2~4 跳 |
| 年级倒置率 | 高年级指向低年级的 PREREQUISITE 占比 | ≤5%（惩罚处理后） |
| 置信度分布 | 高置信度(≥0.8)关系占比 | ≥60% |

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§5.6 多证据融合、§九 验证方案）
