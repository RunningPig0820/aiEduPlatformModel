# 存疑挂起闭环与联调修复

> summary: 存疑挂起闭环三环：落 PENDING obs→学生 vote 转正→维护任务重判；联调 4 bug（非确定性/WEAK 幻觉/候选恒空/vote 转正）已修复。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D7-存疑挂起闭环与联调修复.md
> 类别：架构设计

---

### D7：存疑挂起闭环 + 联调修复

> 检索摘要：存疑挂起闭环三环：落 PENDING obs→学生 vote 转正→维护任务重判；联调 4 bug（非确定性/WEAK 幻觉/候选恒空/vote 转正）已修复。

#### 存疑挂起闭环三环

产品闭环「存疑挂起来 → 学生选择/后续任务补充」三环全通：

```
analyze 存疑 PENDING
  ├─ 落 PENDING obs（upsertPendingIfAbsent 去重）「挂起来」→ 进 pending-kps，不丢
  ├─ 学生选择 → vote → resolvePendingByStudentTopic 转正该生该题型 PENDING → RESOLVED → 聚合沉淀
  └─ 学生不选 → 维护任务 rejudgePending：LLM 重判 → 高置信转 WEAK → 共现(≥2生)转正 → 聚合沉淀
```

#### 新增仓储方法

新增仓储方法：`upsertPendingIfAbsent`、`resolvePendingByStudentTopic`、`resolveWeakByMaintenance`（均 learning 库 SQL）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D7）｜ 完善文档 09-业务闭环与两域解耦.md
