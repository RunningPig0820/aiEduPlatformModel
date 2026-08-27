# 封闭域约束选择（续）

> summary: 封闭域池约束选择：LLM 只能从学段知识点池选，恒非空+年级锚定+确定性；本期未接线（组件已交付）。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D8-封闭域约束选择-2.md
> 类别：架构设计

---

### D8：封闭域约束选择——题目 → 学段知识点池 → LLM 从池选（恒非空）【本期未接线】（续）

> 检索摘要：封闭域池约束选择：LLM 只能从学段知识点池选，恒非空+年级锚定+确定性；本期未接线（组件已交付）。

#### 信任模型

**信任模型（简化，定）**：
```
池约束选择 → top-1（最可能）+ top-N（候选）
  ├─ top-1 直接落 RESOLVED obs（进数据 → 聚合 → 题型库沉淀）【不管置信多低，无确认也进】
  ├─ 学生确认 top-1 → 已是正确（无操作）
  └─ 学生选别的 → vote → 覆盖 top-1（学生确认 = 正确）→ 纠正 obs + 题型库
```
- **学生确认 = 正确**：vote 是最高权威，覆盖 top-1 关联。
- **无确认 → top-1 进数据**：信任 LLM 池选择 top-1 为「最可能」，让题型库冷启动也能沉淀（学生不参与也长）。
- **错误整理**：错误 top-1 由 vote 纠正 / 维护重判 / 管理端审核（P2）整理（D11 飞轮）。
- 不再依赖「WEAK 等第二信号」作为进库门槛（analyze 的 top-1 直接 RESOLVED）；WEAK 保留给答疑主流程 resolve 的 LLM 消歧（仍排除聚合防幻觉）。

#### 与现有组件关系

**与现有组件关系**：`KpQuestionAnalyzer`（题型识别）降级为「① 题型库命中 + ④ 子池召回」的粗筛器之一，不再是唯一关联入口；`KpLlmDisambiguator`（开放域消歧）退为维护任务重判用（PENDING→WEAK），analyze 关联走 D8 约束选择。grade→stage 复用 `KpCoverageAppService.toStageCode`。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D8，下半）｜ 语雀-决策记录.md D27 ｜ 完善文档 07-题目知识点与图谱关联.md
