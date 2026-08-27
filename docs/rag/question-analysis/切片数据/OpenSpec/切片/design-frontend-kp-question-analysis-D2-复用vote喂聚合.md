# 复用 vote 喂聚合

> summary: 学生确认=复用 vote 喂聚合（落 STUDENT_VOTE+转正 PENDING），两确认入口走同一接口，接口不变。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-kp-question-analysis-D2-复用vote喂聚合.md
> 类别：操作流程

---

### 决策 2：学生确认 = 复用 `vote` 接口，喂聚合任务（不新设计）

> 检索摘要：学生确认=复用 vote 喂聚合（落 STUDENT_VOTE+转正 PENDING），两确认入口走同一接口，接口不变。

题型分析页「确认关联」直接复用 `POST /api/kp/vote { topicLabel, selectedLabel }` → 落 `STUDENT_VOTE + RESOLVED` 观测，并**即时转正该生该题型的 PENDING obs**（待确认清单随之消失）。聚合任务已消费该源（`selectResolved` 扫 kp_uri 非空），跨学生达阈值自动沉淀题型库。

**两个确认入口（方案 a）**：
- **贴题结果确认**：RESOLVED 知识点行、PENDING 候选，均可点「确认」→ vote。
- **待确认清单确认（方案 a）**：掌握度页 pending-kps 待确认项展开候选，每条可「确认」→ vote 转正。复用同一 vote 接口，接口不变，纯前端交互。

理由：**不重复造轮子**——`vote` 链路（含记录 `occurrence_count` 幂等、转正 PENDING、喂聚合）已通，题型分析页与待确认清单只是它的消费入口。这与澄清卡同底层，多入口复用同一能力。方案 a 使 PENDING 态永远可操作（能选、能 vote），不是死胡同。

后端确认：candidates 已做镜像校验，每个候选都能 vote（正常不触发 10003）。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-question-analysis.md`（§决策 2）｜ 语雀-决策记录.md D16/D9
