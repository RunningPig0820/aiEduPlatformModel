# 存疑挂起闭环与联调修复（续）

> summary: 存疑挂起闭环三环：落 PENDING obs→学生 vote 转正→维护任务重判；联调 4 bug（非确定性/WEAK 幻觉/候选恒空/vote 转正）已修复。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D7-存疑挂起闭环与联调修复-2.md
> 类别：架构设计

---

### D7：存疑挂起闭环 + 联调修复（续）

> 检索摘要：存疑挂起闭环三环：落 PENDING obs→学生 vote 转正→维护任务重判；联调 4 bug（非确定性/WEAK 幻觉/候选恒空/vote 转正）已修复。

#### 联调修复记录

**联调 4 bug 修复**：
1. **非确定性** → 全候选遍历（顺序无关）+ prompt 收敛（参考词表强制优先/按把握排序/「无法识别」兜底）+ 数据锚优先；**移除缓存**（提示词 + 功能点而非缓存，用户拍板）。
2. **关联错误（对数方程求解）** → ① 聚合 `findResolved`/`findResolvedByTopicLabels` **排除 WEAK**（LLM 幻觉不进题型库，WEAK 需第二信号转正才入）；② `KpResolution.weak` 标记 → analyze 对 WEAK 降级为候选待确认。
3. **candidates 恒空/时有时无** → 遍历兜底 + WEAK 的 kpLabel 也进候选 + 镜像校验（D5）。
4. **vote 未体现** → `resolvePendingByStudentTopic` 转正 PENDING（待确认清单即时消失）；无 PENDING 才新建。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D7，下半）｜ 完善文档 09-业务闭环与两域解耦.md
