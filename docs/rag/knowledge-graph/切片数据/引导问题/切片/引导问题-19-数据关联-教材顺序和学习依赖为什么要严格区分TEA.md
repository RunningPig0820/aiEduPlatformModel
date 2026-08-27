# 教材顺序和学习依赖为什么要严格区分（TEACHES_BEFORE 和 PREREQUISITE）？
> summary: 数据关联引导问题回答：教材"先教"不等于"必须先学"，教学顺序是章节内弱证据只产 TEACHES_BEFORE，学习依赖是需多源确认的强关系 PREREQUISITE，混用会把"教过"误当"掌握"使路径与诊断失真
> 权威度: 1.0（合成问答答案切片，非原始证据）
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/引导问题/引导问题-19-数据关联-教材顺序和学习依赖为什么要严格区分TEA.md
> 类别：数据关联

**核心结论**：教材"先教"不等于"必须先学"——教学顺序（TEACHES_BEFORE）只表达"章节里先讲到谁"、是弱证据，学习依赖（PREREQUISITE）表达"学 B 前必须先掌握 A"、是需要多证据确认的强关系；混用会把"教过"误当"掌握"，导致学习路径和缺陷诊断失真。

## 分层展开
- **语义差异的典型例子**：勾股定理在圆之前教，学圆却不需要先学勾股定理——教材顺序不是学习依赖（依据：完善文档 06 / 语雀 D8）。
- **落地区分（代码）**：`infer_from_textbook_order` 仅限章节内部按小节顺序生成 TEACHES_BEFORE，conf=1.0、source=textbook_order；LLM 投票产出 PREREQUISITE / PREREQUISITE_CANDIDATE——两条语义严格分开（依据：分析-08 / 完善文档 06）。
- **设计权重表**：教材顺序 0.7（只产 TEACHES_BEFORE）/ LLM 双模型 0.8 / 教师标注 1.0（demo 不做）/ 定义定理依赖 0.85（代码实际落地 0.9）——教学顺序在依赖推理里权重最低（依据：完善文档 06）。
- **为什么必须区分**：单一证据（章节顺序/LLM 直觉）都不可靠，需多源交叉确认；单来源"章节顺序直接转 PREREQUISITE"是早期方案，已演进为"顺序只产 TEACHES_BEFORE、学习依赖多证据融合确认"（依据：完善文档 06）。
- **口径提醒（落地边界）**：`infer_from_textbook_order` 方法存在但未挂 CLI 主流程（融合未接入），当前主链路是 LLM 单路径 + 0.8 分界——区分逻辑在代码里成立，但"融合确认"是设计目标非现状（依据：分析-08 / 完善文档 06）。

## 追问防御
- **可能追问：教学顺序是不是完全没用？** → 不是，作弱证据——章节内部生成 TEACHES_BEFORE（conf=1.0），只是不直接升级成 PREREQUISITE（依据：完善文档 06 / 分析-08）。
- **可能追问：代码里真的区分了吗？** → 逻辑区分真实存在（infer_from_textbook_order 只产 TEACHES_BEFORE，LLM 投票产 PREREQUISITE）；但顺序推断未挂 CLI、三来源融合未接入主链路，要讲清方案与落地边界（依据：分析-08）。
- **可能追问：relateTo 和 PREREQUISITE 呢？** → 语义严格区分——relateTo 是普通语义关联，PREREQUISITE 是学习依赖强关系（依据：完善文档 06）。

> 证据：详见 `4.完善文档/06-前置依赖与学习路径.md` ｜ `3.代码/分析-08-前置依赖推断.md`
