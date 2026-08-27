# 两域解耦 + 手动触发

> summary: 采用两域解耦架构：域A负责题目-题型、域B负责题型-知识点，避免单一环节故障互相影响；聚合改手动触发。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-question-type-mastery-backend-D9-两域解耦手动触发.md
> 类别：架构设计

---

### Decision 9：两域解耦 + 手动触发（面试项目不做定时）

> 检索摘要：采用两域解耦架构：域A负责题目-题型、域B负责题型-知识点，避免单一环节故障互相影响；聚合改手动触发。

**本期只记录「题目→题型」**，与「题型→知识点」完全解耦：

```
域 A「题目→题型」（本期，掌握度）          域 B「题型→知识点」（保留不动）
  题目落库 → 向量聚集 → 掌握表累计平均        obs / 题型库 / 别名表 独立存在
  只消费题目记录，不依赖域 B                 不消费掌握度链路
  ↑ 一个环节故障不影响另一个，反之亦然
```

- **去定时**：移除 `KpBatchScheduler` 的 `@Scheduled`（aggregate 3:17 / maintain 3:37），聚合/维护改**按钮手动触发**——现有 `POST /api/kp/aggregation/run`（ADMIN）已具备；批量聚集新增手动接口（ADMIN 按钮）。
- **为什么手动**：面试项目不引入定时任务复杂度；聚合按需即时触发（联调/演示手动跑即可），掌握度链路不受聚合节奏影响。
- **canonical 共享**：两域共享 canonical 名（都是「鸡兔同笼」），经别名表作为收敛接缝——域 A 的向量归并写别名表，域 B 的 analyze 命中自动受益，但**不互相阻塞**。
- **analyze 返回 canonical（前端契约）**：`analyze-question` 返回的 `topicLabel` 必须过聚集 post-process（返回 canonical）——前端用它查 `getMastery`，若返回原始名（「解一元二次方程」）会 miss 掌握表（key=「一元二次方程」）→ 误判「未开始」。**前端联调契约**：
  - `analyze.topicLabel` = canonical（查得到掌握度）
  - `getMastery` PENDING 项 = 题目记录有但 canonical 未归属（域 B 独立化后不再来自 obs）；未开始 = 不在 `items[]`；masteryLevel 分桶 = 掌握表累计平均
  - 题目列表 `score` 与掌握表聚合同源（落库生效分值，可追溯「为什么 64%」）

> 证据：详见 `2.OpenSpec design 决策/design-backend-question-type-mastery-backend.md`（§Decision 9）｜ 语雀-决策记录.md D8/D10 ｜ 完善文档 09-业务闭环与两域解耦.md ｜ 坑档案 J-QT5
