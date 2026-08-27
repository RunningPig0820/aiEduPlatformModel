# 封闭域约束选择

> summary: 封闭域池约束选择：LLM 只能从学段知识点池选，恒非空+年级锚定+确定性；本期未接线（组件已交付）。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D8-封闭域约束选择.md
> 类别：架构设计

---

### D8：封闭域约束选择——题目 → 学段知识点池 → LLM 从池选（恒非空）【本期未接线】

> 检索摘要：封闭域池约束选择：LLM 只能从学段知识点池选，恒非空+年级锚定+确定性；本期未接线（组件已交付）。

> **本期 analyze **不接池约束选择**（前端范围降级：题库 miss → PENDING，空可接受；题库↔知识点关联转「题库和知识点」独立迭代）。池约束编排已抽到 `KpPoolAssociateService`（组件 `KpConstrainedAssociator`/`findLabelsByStage`/粗筛/`keyword` 已交付、有测试），迭代启动时在 analyze ② 处接线即用。**

#### 核心转变与编排流程

**核心转变**：从「开放域自由猜测」→「封闭域约束选择」。当前 analyze 是 LLM 凭空猜题型→猜知识点（两段传递误差 + 猜不中返回空 = 流程死穴）。改为：题目 + 学生学段知识点 label 池 → LLM **只能从池里选**最相关 1-3 个 → 恒返回 top-N（置信低也返回池内最相近，**绝不空**）。

```
① 学段学科：resolveStudentGrade(studentId) → grade → stage；学科固定数学（当前仅数学，subject 预留）
② 题型库命中优先：题型识别命中 canonical/别名 → 权威分布（数据驱动，最快，D5 ① 保留）
③ 题型库 miss → 取学段知识点池 pool（该学段全部数学教材知识点 label，D9）
④ 粗筛子池：题目关键词 / 题型名 name-LIKE 召回（pool 可能 >LLM 上下文，先缩子池）
   - 子池空 → 回退全池截断（前 MAX=200，按章节顺序）
⑤ LLM 约束选择（KpConstrainedAssociator）：只能从子池选 1-3 最相关
   - prompt 强制「必须从池里选，不允许输出池外内容，不允许说无法确定」
   - LLM 失败 → 回退子池前 N 个（确定性兜底）
⑥ 结果恒非空：top-N 全为池内 label（天然镜像可 vote）；高置信 top1 → RESOLVED，否则 PENDING + candidates
```

#### 收益

**收益**：① **恒非空**——LLM 从有限池选必然命中，消灭「空候选死穴」；② **年级锚定**——池按学段过滤，消灭「小学鸡兔同笼→高中对数方程」跨学段错误；③ **确定性**——池确定，同文本结果稳定；④ **数据锚**——池来自教材知识点（镜像），非 LLM 幻觉。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D8）｜ 语雀-决策记录.md D27 ｜ 完善文档 07-题目知识点与图谱关联.md
